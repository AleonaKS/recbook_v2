from bs4 import BeautifulSoup
import requests
import pandas as pd


def get_book_links(url):
    response = requests.get(url)
    data = response.text
    soup = BeautifulSoup(data, 'html.parser')
    book_links = soup.find_all('a', class_='product-card__title')
    return [link.get('href') for link in book_links]

def get_book_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    safe_get_text = lambda element: element.get_text(strip=True) if element else None
    safe_get_meta_content = lambda element: element['content'] if element else None
    safe_get_text_with_replacement = lambda element, to_replace, replacement: element.get_text(strip=True).replace(to_replace, replacement) if element else None

    isbn = safe_get_text(soup.select_one('.product-detail-features__item-title:contains("ISBN") + .product-detail-features__item-value'))
    soon_element = soup.select_one('a.product-info-badge--green:contains("Скоро")')
    new_element = soup.select_one('a.product-info-badge--green:contains("Новинка")')

    book_info = {
        'isbn': isbn,
        'title': safe_get_text(soup.select_one('h1[itemprop="name"]')),
        'author': safe_get_text(soup.select_one('.product-info-authors__author')),
        'soon': True if soon_element else None,
        'new': True if new_element else None,
        'genre': safe_get_text(soup.select('.product-breadcrumbs__item')[-1].find('span', itemprop='name')),
        'tags': [safe_get_text(tag) for tag in soup.select('.detail-product__tags a')],
        'series': safe_get_text(soup.select_one('a[href*="/series/"]')),
        'cycle_book': safe_get_text_with_replacement(soup.select_one('.product-cycle__header'), 'содержание цикла ', ''),
        'publisher': safe_get_text(soup.select_one('a[itemprop="publisher"]')),
        'the_year_of_publishing': safe_get_text(soup.select_one('span[itemprop="datePublished"]')),
        'number_of_pages': safe_get_text(soup.select_one('span[itemprop="numberOfPages"]')),
        'age_restriction': safe_get_text(soup.select_one('.product-info-age')),
        'cover_type': safe_get_text(soup.select_one('span[itemprop="bookFormat"]')),
        'description': safe_get_text(soup.select_one('.detail-description__text')),
        'rating_value': safe_get_text(soup.select_one('.product-review-range__count')),
        'rating_count': safe_get_meta_content(soup.find('meta', itemprop='reviewCount')),
        'price': safe_get_text(soup.select_one('.product-offer-price__old-price')).replace('₽', '').strip() if safe_get_text(soup.select_one('.product-offer-price__old-price')) else None,
        'image_link': soup.select_one('.product-info-gallery__poster-img')['src'] if soup.select_one('.product-info-gallery__poster-img') else None
    }

    # current_book_title = "Душа меча"
    # book_list = soup.find_all('a', class_='product-cycle-categories__link')
    #
    # for index, book in enumerate(book_list, start=1):
    #     if current_book_title in book.text:
    #         print(f"Номер текущей книги в серии: {index}")
    #         break

    reviews_data = []
    review_elements = soup.find_all('div', class_='product-review-card')

    for review_element in review_elements:
        review_data = {
            'isbn': isbn,
            'comment': safe_get_text(review_element.select_one('.product-review-card__comment')),
            'pros': safe_get_text(review_element.select_one('.product-review-card__pros')),
            'cons': safe_get_text(review_element.select_one('.product-review-card__cons')),
            'rating': safe_get_text(review_element.select_one('.product-review-card__rating .box-none')),
            'user_name': safe_get_text(review_element.find('div', itemprop='author')),
            'review_date': safe_get_meta_content(review_element.find('meta', itemprop='datePublished')),
            'likes': safe_get_text(review_element.find('div', class_='product-review-card__like').find('span')),
            'dislikes': safe_get_text(review_element.find('div', class_='product-review-card__dislike').find('span')),
        }
        reviews_data.append(review_data)
    return book_info, reviews_data


base_url = 'https://www.chitai-gorod.ru'
all_books_info = []
all_reviews = []

for page in range(1, 2):
    page_url = f'{base_url}/catalog/books-18030/hudozhestvennaya-literatura-110001?page={page}'
    book_links = get_book_links(page_url)
    for link in book_links:
        book_info, reviews = get_book_info(base_url + link)
        book_info['url'] = base_url + link
        all_books_info.append(book_info)
        all_reviews.extend(reviews)

books = pd.DataFrame(all_books_info)
reviews = pd.DataFrame(all_reviews)

books['the_year_of_publishing'] = pd.to_numeric(books['the_year_of_publishing'], errors='coerce').fillna(0).astype(int)
books['number_of_pages'] = pd.to_numeric(books['number_of_pages'], errors='coerce').fillna(0).astype(int)
books['rating_count'] = pd.to_numeric(books['rating_count'], errors='coerce').fillna(0).astype(int)
books['price'] = pd.to_numeric(books['price'], errors='coerce').fillna(0).astype(int)

books['age_restriction'] = books['age_restriction'].str.replace('+', '')
books['age_restriction'] = pd.to_numeric(books['age_restriction'], errors='coerce').fillna(0).astype('Int64')

books.to_csv('books_copy.csv', index=False, encoding='utf-8')

reviews.to_csv('reviews_df.csv', index=False, encoding='utf-8')
