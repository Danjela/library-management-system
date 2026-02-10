from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from library.models.borrow_models import BookCopy, Reservation


@transaction.atomic
def reserve_book(*, member, book):
    
    if BookCopy.objects.filter(
        book=book,
        loan__member=member,
        loan__returned_at__isnull=True
    ).exists():
        raise ValidationError("You already borrowed this book")

    if Reservation.objects.filter(
        member=member,
        book=book,
        status=Reservation.Status.ACTIVE
    ).exists():
        raise ValidationError("You already reserved this book")

    available = BookCopy.objects.filter(
        book=book,
        status=BookCopy.Status.AVAILABLE
    ).exists()

    if available:
        raise ValidationError(
            "Book is available, reservation not allowed"
        )

    return Reservation.objects.create(
        member=member,
        book=book,
        expires_at=Reservation.default_expiry(),
    )
