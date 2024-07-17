
from .recommendations.main. collaborative import collaborative_filtering, collaborative_filtering_for_book
from .recommendations.main.noML import noML_genre_cycle_soon, popular, continuation_cycle_books
from .recommendations.main. pytorch import recommend_books_for_user
from .recommendations.main. TF_IDF_Word2Vec import tfidf_word2vec_recommendations, find_similar_books
from .recommendations.main. utility_function import utility_function_recs
from .recommendations.main. svd import recommend_books_svd

from .recommendations.main. processing import data_wrangling


from django.db.models import Q
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
import pandas as pd
from main.models import Book, UserPreference, UserReaction
from main.models import import_books_from_dataframe, import_users_from_dataframe, import_reviews_from_dataframe, import_reaction_from_dataframe


df, books_df, reviews_df, users_df, reactions_df = data_wrangling()

# import_books_from_dataframe(books_df)
# import_users_from_dataframe(users_df)
# import_reviews_from_dataframe(reviews_df)
# import_reaction_from_dataframe(reactions_df)

def combine_recommendations(name):
    collaborative = collaborative_filtering(name)
    actual_reads, recs_utility = utility_function_recs(name)
    recs_user = recommend_books_for_user(name)
    combined_recs = collaborative.union(recs_utility, recs_user)
    return combined_recs


def index(request): 
    sport_books = Book.objects.filter(description__icontains='футбол')
    summer_books = Book.objects.filter(description__icontains='лето')
    name = request.session.get('user_name')
    if name:
        combined_recs = combine_recommendations(name)
        personal_books = recommend_books_svd(name)
        all_recommendations = set(combined_recs).union(set(personal_books))
        all_recommendations_list = list(all_recommendations)
        personal_books = all_recommendations_list
        popular_books, soon_books, news_books = noML_genre_cycle_soon(name)
    else:
        popular_books = popular()
        news_books = Book.objects.filter(new=True).order_by('?')[:30]
        soon_books = Book.objects.filter(soon=True).order_by('?')[:30]
    context = {
        'title': 'Главная страница',
        'personal_books': personal_books,
        'popular_books': popular_books,
        'news_books': news_books,
        'soon_books': soon_books,
        'sport_books': sport_books,
        'summer_books': summer_books
    }
    return render(request, 'main/index.html', context)


def all_books(request, category):
    name = request.session.get('user_name')

    sport_books = Book.objects.filter(description__icontains='футбол')
    summer_books = Book.objects.filter(description__icontains='лето ')

    if name:
        combined_recs = combine_recommendations(name)
        personal_books = recommend_books_svd(name)
        all_recommendations = set(combined_recs).union(set(personal_books))
        all_recommendations_list = list(all_recommendations)
        personal_books = all_recommendations_list
        popular_books, soon_books, news_books = noML_genre_cycle_soon(name)
        if category == 'personal':
            books = personal_books
        elif category == 'popular':
            books = popular_books
        elif category == 'news':
            books = news_books
        elif category == 'soon':
            books = soon_books
        elif category == 'news':
            books = news_books
        elif category == 'soon':
            books = soon_books
        else:
            books = Book.objects.all()
    else:
        books = Book.objects.all()

    context = {
        'personal_books': personal_books,
        'popular_books': popular_books,
        'news_books': news_books,
        'soon_books': soon_books,
        'sport_books': sport_books,
        'summer_books': summer_books
    }
    return render(request, 'main/all_books.html', context)


def book_detail(request, book_id):
    book = get_object_or_404(Book, book_id=book_id)
    context = {
        'title': 'Название',
        'books': book
    }
    return render(request, 'main/book_detail.html', context)

def catalog(request):
    user_name = request.session.get('user_name')
    data = {
        'title': 'Каталог'
    }
    return render(request, 'main/catalog.html', data)

def search(request):
    user_name = request.session.get('user_name')
    data = {
        'title': 'Каталог'
    }
    return render(request, 'main/search.html', data)

def cart(request):
    user_name = request.session.get('user_name')
    data = {
        'title': 'Корзина'
    }
    return render(request, 'main/cart.html', data)

def bookmarks(request):
    user_name = request.session.get('user_name')
    data = {
        'title': 'Закладки'
    }
    return render(request, 'main/bookmarks.html', data)





def login(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:  # Проверка, что имя было введено
            request.session['user_name'] = name  # Установка имени пользователя в сессию
            return redirect('profile')  # Перенаправление на страницу профиля
    return render(request, 'main/login.html')  # Отображение страницы входа

def profile(request):
    name = request.session.get('user_name')
    if name:
        ombined_recs = combine_recommendations(name)
        personal_books = recommend_books_svd(name)
        all_recommendations = set(combined_recs).union(set(personal_books))
        all_recommendations_list = list(all_recommendations)
        personal_books = all_recommendations_list
        return render(request, 'main/profile.html', {
            'name': name,
            'fantasy_books': personal_books
        })
    else:
        return redirect('login')
