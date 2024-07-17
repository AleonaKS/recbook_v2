import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec
from ...models import Book, UserPreference, Review, UserReaction


def preprocess_books():
    books = Book.objects.all()
    books_df = pd.DataFrame(list(books.values()))
    books_df['description'] = books_df['description'].str.lower()
    books_df = books_df.dropna(subset=['description'])
    return books_df


def train_tfidf(books_df):
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(books_df['description'])
    return tfidf, tfidf_matrix


def train_word2vec(books_df):
    books_df['combined_features'] = books_df.apply(
        lambda row: ' '.join([str(row['genre']), str(row['tags']), str(row['description'])]), axis=1)
    sentences = [desc.split() for desc in books_df['combined_features']]
    word2vec_model = Word2Vec(sentences, vector_size=100, window=5, min_count=1, workers=4)
    return word2vec_model


def tfidf_word2vec_recommendations(user_name):
    books_df = preprocess_books()
    tfidf, tfidf_matrix = train_tfidf(books_df)
    word2vec_model = train_word2vec(books_df)
    read_books_isbn = Review.objects.filter(name=user_name).values_list('isbn', flat=True)
    read_books_indices = [books_df.index[books_df['isbn'] == isbn].tolist()[0] for isbn in read_books_isbn]
    read_books_tfidf_vectors = tfidf_matrix[read_books_indices]
    read_books_tfidf_vectors = read_books_tfidf_vectors.toarray()
    user_tfidf_vector = np.mean(read_books_tfidf_vectors, axis=0).reshape(1, -1)
    cosine_similarities = cosine_similarity(user_tfidf_vector, tfidf_matrix)
    tfidf_recommendations_isbn = books_df.iloc[np.argsort(-cosine_similarities[0])]['isbn'].head(10).tolist()
    read_books_word2vec_vectors = [word2vec_model.wv[isbn] for isbn in read_books_isbn if isbn in word2vec_model.wv]
    if read_books_word2vec_vectors:
        user_word2vec_vector = np.mean(read_books_word2vec_vectors, axis=0)
        word2vec_distances = np.linalg.norm(np.array(list(word2vec_model.wv.vectors)) - user_word2vec_vector, axis=1)
        word2vec_recommendations_isbn = books_df.iloc[np.argsort(word2vec_distances)]['isbn'].head(10).tolist()
    else:
        word2vec_recommendations_isbn = []
    recommendations_isbn = list(set(tfidf_recommendations_isbn + word2vec_recommendations_isbn))
    recommendations = Book.objects.filter(isbn__in=recommendations_isbn)
    return recommendations



def find_similar_books(book_isbn, top_n=5):
    books_df = preprocess_books()
    tfidf, tfidf_matrix = train_tfidf(books_df)
    word2vec_model = train_word2vec(books_df)
    book_index = list(Book.objects.values_list('isbn', flat=True)).index(book_isbn)
    tfidf_similarities = cosine_similarity(tfidf_matrix[book_index], tfidf_matrix).flatten()
    book_vector = word2vec_model.wv[book_isbn]
    word2vec_similarities = cosine_similarity([book_vector], word2vec_model.wv.vectors).flatten()
    combined_similarities = (tfidf_similarities + word2vec_similarities) / 2
    similar_indices = np.argsort(-combined_similarities)[1:top_n + 1]
    similar_isbns = [list(Book.objects.values_list('isbn', flat=True))[i] for i in similar_indices]
    similar_books = Book.objects.filter(isbn__in=similar_isbns)
    return similar_books