import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
from .processing import data_wrangling
from ...models import Book, UserPreference, Review, UserReaction

df, books_df, reviews_df, users_df, reactions_df = data_wrangling()


def load_data():
    books_df = pd.DataFrame(list(Book.objects.all().values()))
    users_df = pd.DataFrame(list(UserPreference.objects.all().values()))
    reviews_df = pd.DataFrame(list(Review.objects.all().values()))
    reactions_df = pd.DataFrame(list(UserReaction.objects.all().values()))
    return books_df, users_df, reviews_df, reactions_df


def merge_data(books_df, users_df, reviews_df, reactions_df):
    merged_df = users_df.merge(reactions_df, on='name', how='inner', suffixes=('_user', '_reaction')) \
                        .merge(books_df, on='isbn', how='inner', suffixes=('', '_book')) \
                        .merge(reviews_df, on='isbn', how='inner', suffixes=('', '_review'))
    return merged_df

class BookRecommender(nn.Module):
    def __init__(self, num_users, num_books, embedding_dim=50):
        super(BookRecommender, self).__init__()
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.book_embedding = nn.Embedding(num_books, embedding_dim)
        self.fc1 = nn.Linear(embedding_dim * 2, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)
        self.dropout = nn.Dropout(0.3)

    def forward(self, user_id, book_id):
        user_emb = self.user_embedding(user_id)
        book_emb = self.book_embedding(book_id)
        x = torch.cat([user_emb, book_emb], dim=1)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x.squeeze()


def train_model(model, train_loader, test_loader, optimizer, criterion, epochs=100):
    for epoch in range(epochs):
        model.train()
        for user_input, book_input, ratings in train_loader:
            optimizer.zero_grad()
            outputs = model(user_input, book_input)
            loss = criterion(outputs, ratings)
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            total_loss = 0
            for user_input, book_input, ratings in test_loader:
                outputs = model(user_input, book_input)
                total_loss += criterion(outputs, ratings).item()
            print(f'Epoch {epoch}, Loss: {total_loss / len(test_loader)}')


def get_predictions(model, users_books_df):
    user_tensor = torch.LongTensor(users_books_df['user_id'].values)
    book_tensor = torch.LongTensor(users_books_df['book_id'].values)
    predictions = []
    with torch.no_grad():
        for user, book in zip(user_tensor, book_tensor):
            prediction = model(user.unsqueeze(0), book.unsqueeze(0))
            predictions.append(prediction.item())
    users_books_df['predicted_rating'] = predictions
    return users_books_df


def recommend_books(user_id, users_books_df, top_n=10):
    user_books = users_books_df[users_books_df['user_id'] == user_id]
    user_books = user_books.sort_values(by='predicted_rating', ascending=False)
    top_books = user_books.head(top_n)
    book_ids = top_books['book_id'].tolist()
    recommended_books = Book.objects.filter(id__in=book_ids)
    return recommended_books


# каждый раз обучает модель
# def recommend_books_for_user(user_name):
#     books_df, users_df, reviews_df, reactions_df = load_data()
#     num_users = users_df['user_id'].nunique()
#     num_books = books_df['isbn'].nunique()
#     merged_df = merge_data(books_df, users_df, reviews_df, reactions_df)
#     model = BookRecommender(num_users, num_books)
#     optimizer = optim.Adam(model.parameters(), lr=0.001)
#     criterion = nn.MSELoss()
#
#     merged_df['review_date'] = pd.to_datetime(merged_df['review_date'], format='%d.%m.%Y', utc=True)
#     split_date = pd.Timestamp('2024-01-01', tz='UTC')
#
#     train_df = merged_df[merged_df['review_date'] < split_date]
#     test_df = merged_df[merged_df['review_date'] >= split_date]
#
#     train_df = train_df[['book_id', 'rating', 'user_id']]
#     test_df = test_df[['book_id', 'rating', 'user_id']]
#
#     user_tensor = torch.LongTensor(train_df['user_id'].values)
#     book_tensor = torch.LongTensor(train_df['book_id'].values)
#     ratings_tensor = torch.FloatTensor(train_df['rating'].values)
#
#     dataset = TensorDataset(user_tensor, book_tensor, ratings_tensor)
#     train_loader = DataLoader(dataset, batch_size=64, shuffle=True)
#     test_loader = DataLoader(dataset, batch_size=64, shuffle=False)
#
#     train_model(model, train_loader, test_loader, optimizer, criterion)
#     torch.save(model.state_dict(), 'book_recommender.pth')
#     model.load_state_dict(torch.load('book_recommender.pth'))
#
#     users_books_df = merged_df.copy()
#     users_books_df = get_predictions(model, users_books_df)
#     top_n = 5
#     user_pref = UserPreference.objects.get(name=user_name)
#     user_id = user_pref.user_id
#     recommended_books = recommend_books(user_id, users_books_df, top_n)
#     return recommended_books

def train_and_save_model():
    books_df, users_df, reviews_df, reactions_df = load_data()
    num_users = users_df['user_id'].nunique()
    num_books = books_df['isbn'].nunique()
    merged_df = merge_data(books_df, users_df, reviews_df, reactions_df)

    model = BookRecommender(num_users, num_books)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    merged_df['review_date'] = pd.to_datetime(merged_df['review_date'], format='%d.%m.%Y', utc=True)
    split_date = pd.Timestamp('2024-01-01', tz='UTC')

    train_df = merged_df[merged_df['review_date'] < split_date]
    test_df = merged_df[merged_df['review_date'] >= split_date]

    train_df = train_df[['book_id', 'rating', 'user_id']]
    test_df = test_df[['book_id', 'rating', 'user_id']]

    user_tensor = torch.LongTensor(train_df['user_id'].values)
    book_tensor = torch.LongTensor(train_df['book_id'].values)
    ratings_tensor = torch.FloatTensor(train_df['rating'].values)

    dataset = TensorDataset(user_tensor, book_tensor, ratings_tensor)
    train_loader = DataLoader(dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(dataset, batch_size=64, shuffle=False)

    train_model(model, train_loader, test_loader, optimizer, criterion)
    torch.save(model.state_dict(), 'book_recommender.pth')
    print("Модель сохранена в 'book_recommender.pth'")

if __name__ == "__main__":
    train_and_save_model()


def recommend_books_for_user(user_name):
        books_df, users_df, reviews_df, reactions_df = load_data()
        num_users = users_df['user_id'].nunique()
        num_books = books_df['isbn'].nunique()
        merged_df = merge_data(books_df, users_df, reviews_df, reactions_df)
        model = BookRecommender(num_users, num_books)
        model.load_state_dict(torch.load('book_recommender.pth'))
        model.eval()
        users_books_df = merged_df.copy()
        users_books_df = get_predictions(model, users_books_df)
        top_n = 5
        user_pref = UserPreference.objects.get(name=user_name)
        user_id = user_pref.user_id
        recommended_books = recommend_books(user_id, users_books_df, top_n)
        return recommended_books

