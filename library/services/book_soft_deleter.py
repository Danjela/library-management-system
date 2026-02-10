import logging
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError
from library.models.book_models import Book, BookCopy

logger = logging.getLogger("domain")

def soft_delete_book(*, book: Book):
    active_copies = book.copies.filter(
        status__in=[
            BookCopy.Status.BORROWED,
            BookCopy.Status.RESERVED
        ]
    )

    if active_copies.exists():
        logging.error({
            "event": "book_deletion_failed",
            "reason": "active_copies",
            "book_id": book.id,
            "active_copies_count": active_copies.count(),
        })
        raise ValidationError(
            "Cannot delete a book with borrowed or reserved copies"
        )

    book.is_deleted = True
    book.deleted_at = now()
    book.save()
