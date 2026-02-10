from django.db import transaction
from django.db.models import Q
from datetime import timedelta, timezone

from library.models.book_models import BookCopy
from library.models.borrow_models import Loan, Fine, Reservation

class BorrowingError(Exception):
    pass

@transaction.atomic
def borrow_book(member, book):
    # maybe can be a decorator 
    if not member.is_active:
        raise BorrowingError("Inactive member")

    copy = (
        BookCopy.objects
        .select_for_update()
        .filter(
            book=book,
            status=BookCopy.Status.AVAILABLE
        )
        .first()
    )

    if not copy:
        raise BorrowingError("No available copies")

    active_loans = Loan.objects.filter(
        member=member,
        status=Loan.Status.ACTIVE
    ).count()

    if active_loans >= member.max_books_allowed:
        raise BorrowingError("Borrow limit reached")
    
    if Fine.objects.filter(
        loan__member=member,
        is_paid=False
    ).exists():
        raise BorrowingError("Outstanding fines")
    
    first_reservation = Reservation.objects.filter(
        book=book,
        fulfilled=False
    ).order_by("reserved_at").first()

    if first_reservation and first_reservation.member != member:
        raise BorrowingError("Book reserved by another member")

    # the time in days maybe can be a setting
    loan = Loan.objects.create(
        member=member,
        book_copy=copy,
        due_at=timezone.now() + timedelta(days=14)
    )

    copy.status = BookCopy.Status.BORROWED
    copy.save()

    if first_reservation:
        first_reservation.fulfilled = True
        first_reservation.status = Reservation.Status.FULFILLED
        first_reservation.save()

    return loan