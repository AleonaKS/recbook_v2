from datetime import datetime, timedelta
from django.db.models import Min, Max, F, FloatField, Case, When, Sum
from .processing import data_wrangling

from ...models import Book, UserPreference, Review, UserReaction
df, books_df, reviews_df, users_df, reactions_df = data_wrangling()


def add_reaction(reactions_df, user_id, isbn, reaction_type, duration_viewed, date, evaluation):
    new_data = {
        'user_id': user_id,
        'isbn': isbn,
        'reaction_type': reaction_type,
        'duration_viewed': duration_viewed,
        'date': date,
        'evaluation': evaluation
    }
    reactions_df.loc[len(reactions_df)] = new_data

    # Функция для расчета полезности взаимодействия для каждого пользователя
def calculate_interaction_value_per_user():
        VIEW_VALUE = 1
        BOOKMARK_ADDED_VALUE = 2
        BOOKMARK_REMOVED_PENALTY = -1
        CART_ADDED_VALUE = 3
        CART_REMOVED_PENALTY = -1
        PURCHASE_VALUE = 4
        REVIEW_VALUE = 5
        NO_RATING_PENALTY = -0.5

        # Функция для расчета полезности в зависимости от времени просмотра
        def view_value(duration_viewed):
            return min(VIEW_VALUE * (duration_viewed / 60), VIEW_VALUE * 3)

        # Функция для расчета полезности добавления в закладки
        def bookmark_value(date_added):
            one_week = date_added + timedelta(weeks=1)
            three_months = date_added + timedelta(weeks=12)
            now = datetime.now()
            if now <= one_week:
                return BOOKMARK_ADDED_VALUE
            elif one_week < now <= three_months:
                return BOOKMARK_ADDED_VALUE * 1.5
            else:
                return BOOKMARK_ADDED_VALUE * 0.5

        # Функция для расчета полезности в зависимости от оценки
        def rating_value(rating):
            if rating is None:
                return NO_RATING_PENALTY
            elif rating <= 3:
                return (rating / 3) - 5
            elif rating == 4:
                return 1
            elif rating == 5:
                return 3

        reactions = UserReaction.objects.all()

        # Расчет полезности для каждого взаимодействия
        reactions = reactions.annotate(
            interaction_value=Case(
                When(reaction_type='просмотр', then=view_value(F('duration_viewed'))),
                When(reaction_type='отложено в закладки', then=bookmark_value(F('date'))),
                When(reaction_type='убрано из закладок', then=BOOKMARK_REMOVED_PENALTY),
                When(reaction_type='отложено в корзину', then=CART_ADDED_VALUE),
                When(reaction_type='убрано из корзины', then=CART_REMOVED_PENALTY),
                When(reaction_type='покупка', then=PURCHASE_VALUE + rating_value(F('evaluation'))),
                When(reaction_type='оставлен отзыв', then=REVIEW_VALUE + rating_value(F('evaluation'))),
                default=0,
                output_field=FloatField()
            )
        )
        user_interaction_values = reactions.values('user_id').annotate(total_interaction_value=Sum('interaction_value'))
        return user_interaction_values



def normalize_values(user_interaction_values):
            min_value = user_interaction_values.aggregate(Min('total_interaction_value'))[
                'total_interaction_value__min']
            max_value = user_interaction_values.aggregate(Max('total_interaction_value'))[
                'total_interaction_value__max']

            def normalize_negative(value):
                return (value - min_value) / (0 - min_value)

            def normalize_positive(value):
                return (value - 0) / (max_value - 0)

            user_interaction_values = user_interaction_values.annotate(
                normalized_value=Case(
                    When(total_interaction_value__lt=0, then=normalize_negative(F('total_interaction_value'))),
                    When(total_interaction_value__gt=0, then=normalize_positive(F('total_interaction_value'))),
                    default=0,
                    output_field=FloatField()
                )
            )
            return user_interaction_values


def utility_function_recs(name, top_n=5):
    user_reactions = UserReaction.objects.filter(name=name)
    high_value_books = user_reactions.filter(reaction_type__in=['отложено в корзину', 'покупка', 'оставлен отзыв'])
    high_interaction_books = user_reactions.filter(reaction_type__in=['просмотр', 'добавлено в закладки', 'отложено в корзину'])

    high_value_books = high_value_books.annotate(
        interaction_value=Case(
            When(reaction_type='отложено в корзину', then=3),
            When(reaction_type='покупка', then=4 + F('evaluation')),
            When(reaction_type='оставлен отзыв', then=5 + F('evaluation')),
            default=0,
            output_field=FloatField()
        )
    )
    high_interaction_books = high_interaction_books.annotate(
        interaction_value=Case(
            When(reaction_type='просмотр', then=1),
            When(reaction_type='добавлено в закладки', then=2),
            When(reaction_type='отложено в корзину', then=3),
            default=0,
            output_field=FloatField()
        )
    )
    high_value_isbn = high_value_books.values('isbn').annotate(total_interaction_value=Sum('interaction_value')).order_by('-total_interaction_value')
    high_interaction_isbn = high_interaction_books.values('isbn').annotate(total_interaction_value=Sum('interaction_value')).order_by('-total_interaction_value')

    top_high_value_isbn = list(high_value_isbn.values_list('isbn', flat=True)[:top_n])
    top_high_interaction_isbn = list(high_interaction_isbn.values_list('isbn', flat=True)[:top_n])

    top_high_value_books = Book.objects.filter(isbn__in=top_high_value_isbn)
    top_high_interaction_books = Book.objects.filter(isbn__in=top_high_interaction_isbn)

    return top_high_value_books, top_high_interaction_books

    # 1 - наиболее полезные товары пользователя, на основе которых далее осуществляется
    # поиск похожих книг для дальнейшей рекомендации
    # 2 - книги, с которыми пользователь взаимодействовал, подходят для рекомендации
