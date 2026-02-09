from django.db import transaction
from rest_framework.exceptions import ValidationError
from library.models.book_models import Book, Author, BookCopy


@transaction.atomic
def update_book_with_copies(*, book: Book, data: dict):
    book.title = data["title"]
    book.category = data["category"]
    book.description = data["description"]
    book.published_year = data["published_year"]
    book.save()

    authors = []
    for name in data["authors"]:
        author, _ = Author.objects.get_or_create(name=name)
        authors.append(author)

    book.authors.set(authors)

    incoming = data["copies"]
    existing_copies = {str(c.id): c for c in book.copies.select_for_update()}

    incoming_ids = set()
    to_create = []

    for copy_data in incoming:
        copy_id = str(copy_data.get("id")) if copy_data.get("id") else None

        if copy_id and copy_id in existing_copies:
            copy = existing_copies[copy_id]
            copy.barcode = copy_data["barcode"]
            copy.shelf_location = copy_data["shelf_location"]
            copy.save()
            incoming_ids.add(copy_id)

        else:
            to_create.append(BookCopy(
                book=book,
                barcode=copy_data["barcode"],
                shelf_location=copy_data["shelf_location"],
            ))

    to_delete_ids = set(existing_copies.keys()) - incoming_ids

    protected = BookCopy.objects.filter(
        id__in=to_delete_ids,
        status__in=[
            BookCopy.Status.BORROWED,
            BookCopy.Status.RESERVED,
        ],
    )

    if protected.exists():
        raise ValidationError(
            "Cannot delete borrowed or reserved copies"
        )

    BookCopy.objects.filter(id__in=to_delete_ids).delete()

    BookCopy.objects.bulk_create(to_create)

    return book
