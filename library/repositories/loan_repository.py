from library.models.borrow_models import Loan


class LoanRepository:
    def count_active_by_member(self, member):
        return Loan.objects.filter(member=member, status=Loan.Status.ACTIVE).count()
