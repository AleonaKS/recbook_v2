from django.contrib import admin

from .models import Book, UserPreference, Review, UserReaction

admin.site.register(Book)
admin.site.register(UserPreference)
admin.site.register(Review)
admin.site.register(UserReaction)