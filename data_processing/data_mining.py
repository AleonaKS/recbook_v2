from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np
import pandas as pd
import ast

books = pd.read_csv('/content/books_copy.csv')
reviews = pd.read_csv('/content/reviews_df.csv')

reviews = reviews.dropna(subset=['user_name'])

optimal_clusters = {}

# Векторизация текстовых данных
tfidf_vectorizer = TfidfVectorizer(max_features=1000)
reviews['pros'] = reviews['pros'].fillna(' ')
reviews['cons'] = reviews['cons'].fillna(' ')
reviews['combined_text'] = reviews['comment'] + " " + reviews['pros'] + " " + reviews['cons']
tfidf_matrix = tfidf_vectorizer.fit_transform(reviews['combined_text'])

user_name_counts = reviews['user_name'].value_counts()
frequent_users = user_name_counts[user_name_counts > 100].index
unique_identifiers = {}


# Кластеризация пользователей
for user_name in frequent_users:
    temp_df = reviews[reviews['user_name'] == user_name].copy()
    temp_tfidf_matrix = tfidf_vectorizer.fit_transform(temp_df['combined_text'])
    numerical_features = temp_df[['rating']].to_numpy()
    combined_features = np.hstack((numerical_features, temp_tfidf_matrix.toarray()))

    best_score = -1
    best_k = 0
    for i in range(5, 11):
        kmeans = KMeans(n_clusters=i, random_state=0).fit(combined_features)
        score = silhouette_score(combined_features, kmeans.labels_)
        if score > best_score:
            best_score = score
            best_k = i

    optimal_clusters[user_name] = best_k
    kmeans = KMeans(n_clusters=optimal_clusters[user_name], random_state=0).fit(combined_features)
    temp_df['cluster'] = kmeans.labels_
    temp_df['user_id'] = temp_df['user_name'] + (temp_df['cluster'] + 1).astype(str)
    unique_identifiers[user_name] = temp_df

for user_name, df in unique_identifiers.items():
    reviews.loc[df.index, 'user_id'] = df['user_id']

reviews['user_id'] = reviews['user_id'].fillna(reviews['user_name'])

reviews.to_csv('reviews_df.csv', index=False, encoding='utf-8')



reviews_df = reviews.copy()
books_df = books.copy()

# Создание датафреймов для пользователей и истории их взаимодействия
users_df = pd.DataFrame(columns=['user_id', 'favorite_genres', 'favorite_tags', 'disliked_tags', 'author_subscriptions', 'search_queries'])
users_df['user_id'] = reviews['user_id'].unique()

merged_df = pd.merge(reviews, books, on='isbn')

highly_rated = merged_df[merged_df['rating'].isin([4, 5])]

genre_counts_per_user = highly_rated.groupby(['user_id', 'genre']).size().reset_index(name='count')
favorite_genres_per_user = genre_counts_per_user[genre_counts_per_user['count'] >= 3]
favorite_genre_for_each_user = favorite_genres_per_user.groupby('user_id')['genre'].apply(list).reset_index(name='genre')
users_df = users_df.merge(favorite_genre_for_each_user[['user_id', 'genre']], on='user_id', how='left', suffixes=('', 'favorite_genre'))

author_counts_per_user = highly_rated.groupby(['user_id', 'author']).size().reset_index(name='count')
favorite_author_for_each_user = author_counts_per_user[author_counts_per_user['count'] >= 3]
favorite_author_for_each_user = favorite_author_for_each_user.groupby('user_id')['author'].apply(list).reset_index(name='author')
users_df = users_df.merge(favorite_author_for_each_user[['user_id', 'author']], on='user_id', how='left', suffixes=('', '_favorite_author'))

users_df.rename(columns={'genre': 'favorite_genres', 'author': 'author_subscriptions'}, inplace=True)
users_df = users_df.drop_duplicates(subset='user_id')


def safe_eval_list(str_list):
    try:
        return ast.literal_eval(str_list)
    except ValueError:
        return []


books_df['tags'] = books_df['tags'].apply(lambda x: safe_eval_list(x) if isinstance(x, str) else x)
merged_df = pd.merge(reviews_df, books_df, on='isbn')
tag_counts = merged_df.explode('tags').groupby(['user_id', 'tags']).size().reset_index(name='count')
popular_tags = tag_counts[tag_counts['count'] > 3]
tags_by_user = popular_tags.groupby('user_id')['tags'].apply(list).reset_index(name='popular_tags')
users_df['favorite_tags'] = tags_by_user['popular_tags'].apply(lambda x: x if isinstance(x, list) else [])



reactions_df = pd.DataFrame(columns=['user_id', 'isbn', 'reaction_type', 'duration_viewed'])
reviews_to_reactions = reviews_df[['user_id', 'isbn', 'review_date', 'rating']].copy()
reviews_to_reactions['reaction_type'] = 'оставлен отзыв'
reactions_df = pd.concat([reactions_df, reviews_to_reactions], ignore_index=True)
reactions_df.rename(columns={'review_date': 'date', 'rating': 'evaluation'}, inplace=True)

reactions_df.to_csv('reactions_df.csv', index=False, encoding='utf-8')
users_df.to_csv('users_copy.csv', index=False, encoding='utf-8')


