
import pandas as pd
from ...models import Book, UserPreference, Review, UserReaction
from surprise import SVD, Dataset, Reader
from surprise.model_selection import cross_validate
import pickle


books_df = pd.DataFrame(list(Book.objects.all().values()))
users_df = pd.DataFrame(list(UserPreference.objects.all().values()))
reviews_df = pd.DataFrame(list(Review.objects.all().values()))
reactions_df = pd.DataFrame(list(UserReaction.objects.all().values()))

merged_df = users_df.merge(reactions_df, on='name', how='inner', suffixes=('_user', '_reaction')) \
    .merge(books_df, on='isbn', how='inner', suffixes=('', '_book')) \
    .merge(reviews_df, on='isbn', how='inner', suffixes=('', '_review'))

data = Dataset.load_from_df(merged_df[['user_id', 'book_id', 'rating']], Reader(rating_scale=(1, 10)))
svd = SVD()

def svd_model():
    data = Dataset.load_from_df(merged_df[['user_id', 'book_id', 'rating']], Reader(rating_scale=(1, 10)))
    svd = SVD()
    cross_validate(svd, data, measures=['RMSE', 'MAE'], cv=5, verbose=True)
    trainset = data.build_full_trainset()
    svd.fit(trainset)
    with open('svd_model.pkl', 'wb') as f:
        pickle.dump(svd, f)


# svd_model()

# books_df = pd.DataFrame(list(Book.objects.all().values()))
# users_df = pd.DataFrame(list(UserPreference.objects.all().values()))
# reviews_df = pd.DataFrame(list(Review.objects.all().values()))
# reactions_df = pd.DataFrame(list(UserReaction.objects.all().values()))
#
# merged_df = users_df.merge(reactions_df, on='name', how='inner', suffixes=('_user', '_reaction')) \
#     .merge(books_df, on='isbn', how='inner', suffixes=('', '_book')) \
#     .merge(reviews_df, on='isbn', how='inner', suffixes=('', '_review'))
#
# data = Dataset.load_from_df(merged_df[['user_id', 'book_id', 'rating']], Reader(rating_scale=(1, 10)))
# svd = SVD()
# cross_validate(svd, data, measures=['RMSE', 'MAE'], cv=5, verbose=True)
# trainset = data.build_full_trainset()
# svd.fit(trainset)


def recommend_books_svd(name, n_recommendations=10):
        with open('svd_model.pkl', 'rb') as f:
            svd = pickle.load(f)
        all_books = books_df['book_id'].unique()
        predictions = [svd.predict(name, book_id).est for book_id in all_books]
        pred_df = pd.DataFrame({'book_id': all_books, 'predicted_rating': predictions})
        top_books = pred_df.sort_values(by='predicted_rating', ascending=False).head(n_recommendations)
        recommended_books = []
        for book_id in top_books['book_id']:
            try:
                book = Book.objects.get(book_id=book_id)
                recommended_books.append(book)
            except Book.DoesNotExist:
                continue
        return recommended_books
