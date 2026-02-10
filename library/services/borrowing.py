import logging
from django.db import transaction
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from library.models.book_models import BookCopy
from library.models.borrow_models import Loan, Reservation

from library.repositories.book_copy_repository import BookCopyRepository
from library.repositories.loan_repository import LoanRepository
from library.repositories.fine_repository import FineRepository
from library.repositories.reservation_repository import ReservationRepository

from library.services.specifications.member_specifications import (
    MemberIsActive,
    MemberBelowBorrowLimit,
    MemberHasNoUnpaidFines,
)
from library.services.specifications.reservation_specifications import (
    BookNotReservedByAnother,
)

class BorrowingError(Exception):
    pass

logger = logging.getLogger("domain")

@transaction.atomic
def borrow_book(member, book):
    book_copy_repo = BookCopyRepository()
    loan_repo = LoanRepository()
    fine_repo = FineRepository()
    reservation_repo = ReservationRepository()

    specs = [
        MemberIsActive(),
        MemberHasNoUnpaidFines(fine_repo),
        MemberBelowBorrowLimit(loan_repo),
        BookNotReservedByAnother(reservation_repo),
    ]

    for spec in specs:
        ok = spec.is_satisfied_by(member, book=book)
        if not ok:
            logger.warning({
                "event": "borrow_rejected",
                "reason": getattr(spec, "error_message", "validation_failed"),
                "book_id": getattr(book, "id", None),
                "member_id": getattr(member, "id", None),
            })
            raise BorrowingError(getattr(spec, "error_message", "Validation failed"))

    copy = book_copy_repo.find_available_for_book(book)
    if not copy:
        logger.warning({
            "event": "borrow_rejected",
            "reason": "no_available_copies",
            "book_id": getattr(book, "id", None),
            "member_id": getattr(member, "id", None),
        })
        raise BorrowingError("No available copies")

    loan_days = getattr(settings, "LIBRARY_LOAN_DAYS", 14)
    loan = Loan.objects.create(
        member=member,
        book_copy=copy,
        due_at=timezone.now() + timedelta(days=loan_days)
    )

    copy.status = BookCopy.Status.BORROWED
    copy.save()

    first_reservation = reservation_repo.first_unfulfilled_for_book(book)
    if first_reservation:
        first_reservation.fulfilled = True
        first_reservation.status = Reservation.Status.FULFILLED
        first_reservation.save()

    return loan