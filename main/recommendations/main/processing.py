from django.utils import timezone
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
def data_wrangling():
    books_df = pd.read_csv('datasets/books_df.csv')
    reviews_df = pd.read_csv('datasets/reviews_df.csv')
    users_df = pd.read_csv('datasets/users_df.csv')
    reactions_df = pd.read_csv('datasets/reactions_df.csv')

    books_df['the_year_of_publishing'] = books_df['the_year_of_publishing'].fillna(0)
    books_df['rating_value'] = books_df['rating_value'].fillna(0)
    books_df['author'] = books_df['author'].fillna('Unknown Author')

    books_df['soon'] = books_df['soon'].fillna(False).infer_objects(copy=False)
    books_df['new'] = books_df['new'].fillna(False).infer_objects(copy=False)
    books_df['special_edition'] = books_df['special_edition'].fillna(False).infer_objects(copy=False)

    def remove_prefix(text, prefix):
        if text.startswith(prefix):
            return text[len(prefix):].strip()
        return text

    reviews_df['cons'] = reviews_df['cons'].apply(lambda x: remove_prefix(x, 'Минусы'))
    reviews_df['review_date'] = pd.to_datetime(reviews_df['review_date'], format='%d.%m.%Y')
    reviews_df['review_date'] = reviews_df['review_date'].apply(
        lambda x: timezone.make_aware(x, timezone.get_default_timezone()))

    reactions_df['duration_viewed'] = reactions_df['duration_viewed'].fillna(0)
    reactions_df['date'] = pd.to_datetime(reactions_df['date'], format='%d.%m.%Y')
    reactions_df['date'] = reactions_df['date'].apply(lambda x: timezone.make_aware(x, timezone.get_default_timezone()))

    df = pd.merge(books_df, reviews_df, on='isbn', how='left')
    df = pd.merge(df, users_df, on='name', how='left')
    df = pd.merge(df, reactions_df, on=['name', 'isbn'], how='left')
    df = df.dropna(subset=['rating'])
    return df, books_df, reviews_df, users_df, reactions_df
