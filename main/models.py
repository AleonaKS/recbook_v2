from django.core.validators import validate_comma_separated_integer_list

from django.db import models
import re
import pandas as pd
from django.utils.timezone import make_aware
from datetime import datetime

# Модель для книг
class Book(models.Model):
    book_id = models.IntegerField(unique=True)
    isbn = models.CharField(max_length=60)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    soon = models.BooleanField(default=False)
    new = models.BooleanField(default=False)
    genre = models.CharField(max_length=255)
    tags = models.CharField(max_length=255)
    series = models.CharField(max_length=100, null=True, blank=True)
    cycle_book = models.CharField(max_length=100, null=True, blank=True)
    publisher = models.CharField(max_length=30)
    the_year_of_publishing = models.IntegerField()
    number_of_pages = models.IntegerField()
    age_restriction = models.IntegerField()
    cover_type = models.CharField(max_length=50)
    description = models.TextField()
    rating_value = models.FloatField(default=0)
    rating_count = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_link = models.URLField()
    url = models.URLField()
    special_edition = models.BooleanField(default=False)

    def __str__(self):
        return self.title
class UserPreference(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(default=0, unique=True)
    name = models.CharField(max_length=100)
    favorite_genres = models.CharField(max_length=255)
    favorite_tags = models.CharField(max_length=255)
    disliked_tags = models.CharField(max_length=255)
    author_subscriptions = models.CharField(max_length=255)
    search_queries = models.TextField()
    cluster_label = models.IntegerField(default=-1)

    def __str__(self):
        return self.name

# Модель для отзывов
class Review(models.Model):
    review_id = models.IntegerField(default=0, unique=True)
    isbn = models.CharField(max_length=60)
    name = models.CharField(max_length=100)
    comment = models.TextField()
    pros = models.TextField()
    cons = models.TextField()
    rating = models.FloatField()
    review_date = models.DateTimeField()
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class UserReaction(models.Model):
    reaction_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    isbn = models.CharField(max_length=60)
    date = models.DateTimeField()
    reaction_type = models.CharField(max_length=20)
    duration_viewed = models.IntegerField()
    evaluation = models.IntegerField()

    def __str__(self):
        return self.isbn


def import_books_from_dataframe(books_df):
    Book.objects.bulk_create([
        Book(
            book_id=row['book_id'],
            isbn=row['isbn'],
            title=row['title'],
            author=row['author'],
            soon=row['soon'],
            new=row['new'],
            genre=row['genre'],
            tags=row['tags'],
            series=row['series'],
            cycle_book=row['cycle_book'],
            publisher=row['publisher'],
            the_year_of_publishing=row['the_year_of_publishing'],
            number_of_pages=row['number_of_pages'],
            age_restriction=row['age_restriction'],
            cover_type=row['cover_type'],
            description=row['description'],
            rating_value=row['rating_value'],
            rating_count=row['rating_count'],
            price=row['price'],
            image_link=row['image_link'],
            url=row['url'],
            special_edition=row['special_edition']
        )
        for _, row in books_df.iterrows()
    ])



def import_users_from_dataframe(users_df):
    UserPreference.objects.bulk_create([
        UserPreference(
            user_id=row['user_id'],
            name=row['name'],
            favorite_tags=row['favorite_tags'],
            disliked_tags=row['disliked_tags'],
            favorite_genres=row['favorite_genres'],
            author_subscriptions=row['author_subscriptions'],
            search_queries=row['search_queries']
        )
        for _, row in users_df.iterrows()
    ])


def import_reviews_from_dataframe(reviews_df):
    Review.objects.bulk_create([
        Review(
            review_id=row['review_id'],
            name=row['name'],
            isbn=row['isbn'],
            comment=row['comment'],
            pros=row['pros'],
            cons=row['cons'],
            rating=row['rating'],
            review_date=row['review_date'],
            likes=row['likes'],
            dislikes=row['dislikes']
        )
        for _, row in reviews_df.iterrows()
    ])


def import_reaction_from_dataframe(reactions_df):
    reactions_df['date'] = pd.to_datetime(reactions_df['date'], format='mixed')
    reactions_df['date'] = reactions_df['date'].apply(lambda x: make_aware(datetime.combine(x.date(), x.time())))

    UserReaction.objects.bulk_create([
        UserReaction(
            reaction_id=row['reactions_id'],
            name=row['name'],
            isbn=row['isbn'],
            date=row['date'],
            reaction_type=row['reaction_type'],
            duration_viewed=row['duration_viewed'],
            evaluation=row['evaluation']
        )
        for _, row in reactions_df.iterrows()
    ])

