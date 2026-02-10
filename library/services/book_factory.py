from library.models.book_models import Book, Author, BookCopy
from django.db import transaction


@transaction.atomic
def create_book_with_copies(
    *,
    title,
    isbn,
    category,
    description,
    published_year,
    authors,
    copies
):
    book = Book.objects.create(
        title=title,
        isbn=isbn,
        category=category,
        description=description,
        published_year=published_year,
    )

    author_objects = []
    for name in authors:
        author, _ = Author.objects.get_or_create(name=name)
        author_objects.append(author)

    book.authors.set(author_objects)

    BookCopy.objects.bulk_create([
        BookCopy(
            book=book,
            barcode=copy["barcode"],
            shelf_location=copy["shelf_location"],
        )
        for copy in copies
    ])

    return book