from library.models.borrow_models import Fine


class FineRepository:
    def member_has_unpaid_fines(self, member):
        return Fine.objects.filter(loan__member=member, is_paid=False).exists()
