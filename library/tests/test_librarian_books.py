from rest_framework.test import APITestCase
from rest_framework import status

from library.models.book_models import Book
from factories import create_user, create_book


class LibrarianBookCRUDTests(APITestCase):

    def setUp(self):
        self.librarian = create_user(is_librarian=True)
        self.client.force_authenticate(user=self.librarian)

    def test_librarian_can_create_book(self):
        payload = {
            "title": "Clean Architecture",
            "isbn": "1234567890123",
            "category": "Tech",
            "description": "Architecture book",
            "published_year": 2023,
            "authors": ["Uncle Bob"],
            "copies": [
                {"barcode": "BC-1", "shelf_location": "A1"},
                {"barcode": "BC-2", "shelf_location": "A1"},
            ],
        }

        response = self.client.post(
            "/api/librarian/books/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 1)

    def test_librarian_can_view_copies(self):
        book = create_book(copies=2)

        response = self.client.get(
            f"/api/librarian/books/{book.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("copies", response.data)
        self.assertEqual(len(response.data["copies"]), 2)
