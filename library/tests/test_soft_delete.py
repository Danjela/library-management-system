from rest_framework.test import APITestCase
from rest_framework import status

from library.models.book_models import BookCopy
from factories import create_user, create_book


class BookSoftDeleteTests(APITestCase):

    def setUp(self):
        self.librarian = create_user(is_librarian=True)
        self.client.force_authenticate(user=self.librarian)

    def test_soft_delete_book(self):
        book = create_book()

        response = self.client.delete(
            f"/api/librarian/books/{book.id}/delete/"
        )

        book.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(book.is_deleted)

    def test_cannot_delete_if_borrowed_copy_exists(self):
        book = create_book(copy_status=BookCopy.Status.BORROWED)

        response = self.client.delete(
            f"/api/librarian/books/{book.id}/delete/"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
