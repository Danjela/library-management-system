import logging
from django.utils import timezone
from django.db import transaction
from library.models.borrow_models import BookCopy, Loan, Fine, Reservation

# currency units per day consider moving to settings
DAILY_FINE_RATE = 1.50

logger = logging.getLogger("domain")

def calculate_fine(loan: Loan) -> float:
    if loan.returned_at <= loan.due_at:
        return 0

    days_late = (loan.returned_at - loan.due_at).days
    return days_late * DAILY_FINE_RATE


@transaction.atomic
def return_book(loan : Loan) -> float:
    if loan.status != Loan.Status.ACTIVE:
        logger.error({
            "event": "return_failed",
            "reason": "loan_not_active",
            "loan_id": loan.id,
            "member_id": loan.member.id,
            "book_copy_id": loan.book_copy.id,
        })
        raise ValueError("Loan already closed")
    
    loan.returned_at = timezone.now()

    fine_amount = calculate_fine(loan)
    if fine_amount > 0:
        loan.status = Loan.Status.OVERDUE
        Fine.objects.create(
            loan=loan,
            amount=fine_amount
        )
        logger.error({
            "event": "book_returned_with_fine",
            "loan_id": loan.id,
            "member_id": loan.member.id,
            "book_copy_id": loan.book_copy.id,
            "fine_amount": fine_amount,
        })
    else:
        loan.status = Loan.Status.RETURNED

    loan.save()

    copy = loan.book_copy

    has_reservations = Reservation.objects.filter(
        book=copy.book,
        fulfilled=False
    ).exists()

    copy.status = (
        BookCopy.Status.RESERVED
        if has_reservations
        else BookCopy.Status.AVAILABLE
    )
    copy.save()

    return fine_amount