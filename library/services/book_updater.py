import logging
from django.db import transaction
from rest_framework.exceptions import ValidationError
from library.models.book_models import Book, Author, BookCopy


@transaction.atomic
def update_book_with_copies(*, book: Book, data: dict):
    book.title = data.get("title", book.title)
    book.category = data.get("category", book.category)
    book.description = data.get("description", book.description)
    book.published_year = data.get("published_year", book.published_year)
    book.save()

    authors = []
    incoming_authors = data.get("authors", None)
    if incoming_authors is None:
        authors = list(book.authors.all())
    else:
        for entry in incoming_authors:
            if isinstance(entry, dict):
                name = entry.get("name")
            else:
                name = entry
            if not name:
                continue
            author, _ = Author.objects.get_or_create(name=name)
            authors.append(author)

    book.authors.set(authors)

    incoming = data.get("copies", [])
    if incoming is None:
        incoming = []
    if not isinstance(incoming, list):
        raise ValidationError("`copies` must be a list")

    existing_copies = {str(c.id): c for c in book.copies.select_for_update()}

    incoming_ids = set()
    to_create = []

    for copy_data in incoming:
        if not isinstance(copy_data, dict):
            raise ValidationError("Each copy item must be an object with keys 'barcode' and 'shelf_location'")

        copy_id = str(copy_data.get("id")) if copy_data.get("id") else None

        barcode = copy_data.get("barcode")
        shelf_location = copy_data.get("shelf_location")
        if not barcode or not shelf_location:
            raise ValidationError("Each copy must include 'barcode' or 'shelf_location'")

        if copy_id and copy_id in existing_copies:
            copy = existing_copies[copy_id]
            copy.barcode = barcode
            copy.shelf_location = shelf_location
            copy.save()
            incoming_ids.add(copy_id)

        else:
            to_create.append(BookCopy(
                book=book,
                barcode=barcode,
                shelf_location=shelf_location,
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
        logging.error({
            "event": "book_update_failed",
            "reason": "active_copies_on_update",
            "book_id": book.id,
            "protected_copies_count": protected.count(),
        })
        raise ValidationError(
            "Cannot delete borrowed or reserved copies"
        )

    BookCopy.objects.filter(id__in=to_delete_ids).delete()

    BookCopy.objects.bulk_create(to_create)

    return book
