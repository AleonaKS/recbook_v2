
from ...models import Book, UserPreference, Review
from django.db.models import F

def read_books(user_name):
    user_pref = UserPreference.objects.get(name=user_name)
    user_reviews = Review.objects.filter(name=user_name)
    book_isbns = user_reviews.values_list('isbn', flat=True).distinct()
    read_books = Book.objects.filter(isbn__in=book_isbns)
    read_books_list = list(read_books.values_list('isbn', flat=True))
    return user_pref, read_books_list

def noML_genre_cycle_soon(user_name):
    user_pref, read_books_list = read_books(user_name)
    recommended_books = []
    favorite_genres = [genre.replace("'", "").strip() for genre in user_pref.favorite_genres.split(',')]
    for genre in favorite_genres:
        genre_books = Book.objects.filter(
            genre__icontains=genre,
            rating_value__gte=4.5,
            rating_count__gt=50
        ).annotate(
            score=F('rating_value') * F('rating_count')
        ).order_by('-score')[:3]
        recommended_books.extend(list(genre_books))

    favorite_tags = [tags.replace("'", "").strip() for tags in user_pref.favorite_tags.split(',')]
    for tags in favorite_tags:
        tag_books = Book.objects.filter(
            tags__icontains=tags,
            rating_value__gte=4.5,
            rating_count__gt=50
        ).annotate(
            score=F('rating_value') * F('rating_count')
        ).order_by('-score')[:3]
        recommended_books.extend(list(tag_books))

    soon_recbook = []
    soon_books = Book.objects.filter(
        soon=True,
        genre__in=favorite_genres
    ).distinct()
    new_recbook = []
    new_books = Book.objects.filter(
        new=True,
        genre__in=favorite_genres
    ).distinct()

    soon_recbook.extend(list(soon_books))
    new_recbook.extend(list(new_books))

    soon_unique_books = {book.isbn: book for book in soon_recbook if book.isbn not in read_books_list}.values()
    unique_soon_books = list(soon_unique_books)
    new_unique_books = {book.isbn: book for book in new_recbook if book.isbn not in read_books_list}.values()
    unique_new_books = list(new_unique_books)
    unique_recommended_books = {book.isbn: book for book in recommended_books if book.isbn not in read_books_list}.values()
    unique_recommended_books = list(unique_recommended_books)
    return unique_recommended_books, unique_soon_books, unique_new_books



def popular():
    books = Book.objects.filter(
        rating_value__gte=4.5,
        rating_count__gt=50
    ).annotate(
        score=F('rating_value') * F('rating_count')
    ).order_by('-score')[:50]
    return books


def continuation_cycle_books(user_name):
    user_pref, read_books_list = read_books(user_name)
    cycle_books = []
    for book in read_books:
        if book.cycle:
            cycle_books.extend(Book.objects.filter(cycle=book.cycle).exclude(isbn__in=read_books_list))
    unique_cycle_books = {book.isbn: book for book in cycle_books}.values()
    unique_cycle_books = list(unique_cycle_books)
    return unique_cycle_books