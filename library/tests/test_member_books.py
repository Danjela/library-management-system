from rest_framework.test import APITestCase
from rest_framework import status

from library.models.book_models import BookCopy
from factories import create_user, create_book


class MemberBookListTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        self.client.login(username=self.user.username, password="password123")

        create_book(title="Django Basics", copies=2)
        create_book(
            title="Unavailable Book",
            copies=1,
            copy_status=BookCopy.Status.BORROWED,
        )

    def test_member_sees_only_available_books(self):
        response = self.client.get("/api/public/books/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [b["title"] for b in response.data["results"]]

        self.assertIn("Django Basics", titles)
        self.assertNotIn("Unavailable Book", titles)

    def test_search_by_title(self):
        response = self.client.get("/api/public/books/?title=django")
        self.assertEqual(len(response.data["results"]), 1)

    def test_pagination_applied(self):
        response = self.client.get("/api/public/books/?page=1")
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)


class MemberBookDetailTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        self.client.login(username=self.user.username, password="password123")
        self.book = create_book()

    def test_member_does_not_see_copies(self):
        response = self.client.get(
            f"/api/public/books/{self.book.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("copies", response.data)
