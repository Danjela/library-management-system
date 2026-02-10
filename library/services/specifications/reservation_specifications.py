from library.repositories.reservation_repository import ReservationRepository


class BookNotReservedByAnother:
    error_message = "Book reserved by another member"

    def __init__(self, reservation_repo: ReservationRepository = None):
        self.reservation_repo = reservation_repo or ReservationRepository()

    def is_satisfied_by(self, member, book=None, **_):
        first = self.reservation_repo.first_unfulfilled_for_book(book)
        if first and first.member != member:
            return False
        return True
