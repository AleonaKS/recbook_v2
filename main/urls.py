from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog', views.catalog, name='catalog'),
    path('cart', views.cart, name='cart'),
    path('bookmarks', views.bookmarks, name='bookmarks'),
    path('profile/', views.profile, name='profile'),
    path('login/', views.login, name='login'),
    path('search', views.search, name='search'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('all_books/<str:category>/', views.all_books, name='all_books'),


]