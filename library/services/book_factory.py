from library.models.book_models import Book, Author, BookCopy
from django.db import transaction

from library.services.book_queries import get_available_books


@transaction.atomic
def create_book_with_copies(
    *,
    title,
    isbn,
    category,
    description,
    published_year,
    author_names,
    copies
):
    book = Book.objects.create(
        title=title,
        isbn=isbn,
        category=category,
        description=description,
        published_year=published_year,
    )

    authors = []
    for name in author_names:
        author, _ = Author.objects.get_or_create(name=name)
        authors.append(author)

    book.authors.set(authors)

    BookCopy.objects.bulk_create([
        BookCopy(
            book=book,
            barcode=copy["barcode"],
            shelf_location=copy["shelf_location"],
        )
        for copy in copies
    ])

    return book