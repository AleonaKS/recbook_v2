from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import Book, UserPreference, Review, UserReaction
import pandas as pd

class Command(BaseCommand):
    help = 'Load books from a dataframe into the database using bulk_create'

    def handle(self, *args, **kwargs):
        books_df = pd.read_csv('datasets/books_copy.csv')
        reviews_df = pd.read_csv('datasets/reviews_df.csv')
        users_df = pd.read_csv('datasets/users_df.csv')
        reactions_df = pd.read_csv('datasets/reactions_df.csv')
        books_df['book_id'] = range(0, len(books_df))

        books_df['the_year_of_publishing'].fillna(0, inplace=True)
        books_df['rating_value'].fillna(0, inplace=True)

        books_df.rename(columns={'ono': 'name'}, inplace=True)
        reviews_df.rename(columns={'ono': 'name'}, inplace=True)
        users_df.rename(columns={'ono': 'name'}, inplace=True)
        reactions_df.rename(columns={'ono': 'name'}, inplace=True)

        books_df['author'].fillna('Unknown Author', inplace=True)
        books_df['soon'].fillna(False, inplace=True)
        books_df['new'].fillna(False, inplace=True)
        books_df['special_edition'].fillna(False, inplace=True)

        book_instances = [
            Book(
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
            for index, row in books_df.iterrows()
        ]

        # Используйте bulk_create для загрузки всех объектов одной операцией
        with transaction.atomic():
            Book.objects.bulk_create(book_instances, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS('Successfully loaded all books into the database'))

        users_preferences_instances = [
            UserPreference(
                user_id=row['user_id'],
                name=row['name'],
                favorite_tags=row['favorite_tags'],
                disliked_tags=row['disliked_tags'],
                favorite_genres=row['favorite_genres'],
                author_subscriptions=row['author_subscriptions'],
                search_queries=row['search_queries']
            )
            for index, row in users_df.iterrows()
        ]
        with transaction.atomic():
            UserPreference.objects.bulk_create(users_preferences_instances, ignore_conflicts=True)

        reviews_instances = [
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
            for index, row in reviews_df.iterrows()
        ]
        with transaction.atomic():
            Review.objects.bulk_create(reviews_instances, ignore_conflicts=True)

        reactions_instances = [
            UserReaction(
                review_id=row['review_id'],
                name=row['name'],
                isbn=row['isbn'],
                date=row['date'],
                reaction_type=row['reaction_type'],
                duration_viewed=row['duration_viewed'],
                evaluation=row['evaluation']
            )
            for index, row in reactions_df.iterrows()
        ]
        with transaction.atomic():
            UserReaction.objects.bulk_create(reactions_instances, ignore_conflicts=True)
