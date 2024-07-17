import sklearn
from django.db.models import F
from django.db.models import Q
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from ...models import Book, UserPreference, Review, UserReaction
from .utility_function import utility_function_recs

from .processing import data_wrangling
df, books_df, reviews_df, users_df, reactions_df = data_wrangling()


def get_user_books(user_name):
    top_high_value_books, top_high_interaction_books = utility_function_recs(user_name)
    return top_high_value_books


def build_user_book_matrix(user_name):
    user_pref = UserPreference.objects.get(name=user_name)
    if user_pref.cluster_label == -1:
        all_users = UserPreference.objects.all()
    else:
        all_users = UserPreference.objects.filter(cluster_label=user_pref.cluster_label)
    user_book_matrix = {}
    for user in all_users:
        reviews = get_user_books(user.name)
        user_book_matrix[user.name] = {review.isbn: review.rating_value for review in reviews}
    return user_book_matrix


def collaborative_filtering(user_name, top_n=10):
    user_book_matrix = build_user_book_matrix(user_name)
    user_ids = list(user_book_matrix.keys())
    book_ids = list({isbn for reviews in user_book_matrix.values() for isbn in reviews.keys()})

    matrix = np.zeros((len(user_ids), len(book_ids)))
    for i, user in enumerate(user_ids):
        for j, book in enumerate(book_ids):
            if book in user_book_matrix[user]:
                matrix[i, j] = user_book_matrix[user][book]

    user_index = user_ids.index(user_name)
    similarity_matrix = cosine_similarity(matrix)
    similar_users = np.argsort(-similarity_matrix[user_index])[1:]

    recommended_books = {}
    for similar_user in similar_users:
        similar_user_id = user_ids[similar_user]
        for book, rating_value in user_book_matrix[similar_user_id].items():
            if book not in user_book_matrix[user_name]:
                if book not in recommended_books:
                    recommended_books[book] = 0
                recommended_books[book] += rating_value

    recommended_books = sorted(recommended_books.items(), key=lambda x: x[1], reverse=True)
    book_ids = [book for book, rating_value in recommended_books[:top_n]]
    books = Book.objects.filter(isbn__in=book_ids)
    return books



def collaborative_filtering_for_book(book_isbn, top_n=10):
    all_reviews = Review.objects.all()
    user_book_matrix = {}
    for review in all_reviews:
        if review.user.name not in user_book_matrix:
            user_book_matrix[review.user.name] = {}
        user_book_matrix[review.user.name][review.book.isbn] = review.rating_value

    user_ids = list(user_book_matrix.keys())
    book_ids = list({isbn for reviews in user_book_matrix.values() for isbn in reviews.keys()})

    matrix = np.zeros((len(user_ids), len(book_ids)))
    for i, user in enumerate(user_ids):
        for j, book in enumerate(book_ids):
            if book in user_book_matrix[user]:
                matrix[i, j] = user_book_matrix[user][book]

    book_index = book_ids.index(book_isbn)
    similarity_matrix = cosine_similarity(matrix.T)
    similar_books = np.argsort(-similarity_matrix[book_index])[1:]

    recommended_books = [book_ids[i] for i in similar_books[:top_n]]
    books = Book.objects.filter(isbn__in=recommended_books)
    return books
