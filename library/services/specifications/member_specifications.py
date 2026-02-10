from library.repositories.loan_repository import LoanRepository
from library.repositories.fine_repository import FineRepository
from django.conf import settings


class MemberIsActive:
    error_message = "Inactive member"

    def is_satisfied_by(self, member, **_):
        return bool(getattr(member, "is_active", False))


class MemberBelowBorrowLimit:
    error_message = "Borrow limit reached"

    def __init__(self, loan_repo: LoanRepository = None):
        self.loan_repo = loan_repo or LoanRepository()

    def is_satisfied_by(self, member, **_):
        limit = getattr(settings, "LIBRARY_MAX_BOOKS_ALLOWED", None)
        if limit is None:
            limit = 5
        return self.loan_repo.count_active_by_member(member) < limit


class MemberHasNoUnpaidFines:
    error_message = "Outstanding fines"

    def __init__(self, fine_repo: FineRepository = None):
        self.fine_repo = fine_repo or FineRepository()

    def is_satisfied_by(self, member, **_):
        return not self.fine_repo.member_has_unpaid_fines(member)
