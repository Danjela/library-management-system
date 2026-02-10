from library.models.borrow_models import Reservation


class ReservationRepository:
    def first_unfulfilled_for_book(self, book):
        return (
            Reservation.objects
            .filter(book=book, fulfilled=False)
            .order_by("reserved_at")
            .first()
        )
