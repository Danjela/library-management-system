from library.models.book_models import BookCopy


class BookCopyRepository:
    def find_available_for_book(self, book):
        return (
            BookCopy.objects
            .select_for_update()
            .filter(book=book, status=BookCopy.Status.AVAILABLE)
            .first()
        )
