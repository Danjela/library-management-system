from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from library.models.book_models import BookCopy
from library.models.borrow_models import Member, Loan, Fine, Reservation
from factories import create_user, create_book


class ReturnBookAPITests(APITestCase):

    def setUp(self):
        """Set up test user, member, and book for each test"""
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.member = Member.objects.get(user=self.user)
        
        self.book = create_book(copies=1)
        self.book_copy = self.book.copies.first()

    def test_return_book_successfully_without_fine(self):
        """Test returning a book on time without any fine"""
        # Create an active loan due in the future
        loan = Loan.objects.create(
            member=self.member,
            book_copy=self.book_copy,
            due_at=timezone.now() + timedelta(days=5),
            status=Loan.Status.ACTIVE
        )
        self.book_copy.status = BookCopy.Status.BORROWED
        self.book_copy.save()

        response = self.client.post("/api/books/return/", {
            "loan_id": loan.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "RETURNED")
        self.assertEqual(response.data["fine"], 0)

        # Verify loan status updated
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.RETURNED)
        self.assertIsNotNone(loan.returned_at)

        # Verify book copy is available
        self.book_copy.refresh_from_db()
        self.assertEqual(self.book_copy.status, BookCopy.Status.AVAILABLE)

        # Verify no fine created
        self.assertFalse(Fine.objects.filter(loan=loan).exists())

    def test_return_book_with_late_fine(self):
        """Test returning a book late creates a fine"""
        # Create a loan that's overdue
        due_date = timezone.now() - timedelta(days=2)
        loan = Loan.objects.create(
            member=self.member,
            book_copy=self.book_copy,
            due_at=due_date,
            status=Loan.Status.ACTIVE
        )
        self.book_copy.status = BookCopy.Status.BORROWED
        self.book_copy.save()

        response = self.client.post("/api/books/return/", {
            "loan_id": loan.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreater(response.data["fine"], 0)

        # Verify loan status is OVERDUE
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.OVERDUE)

        # Verify fine was created
        fine = Fine.objects.get(loan=loan)
        self.assertEqual(fine.amount, 3.00)  # 2 days * 1.50 per day

    def test_return_already_returned_loan(self):
        """Test cannot return a loan that's already returned"""
        loan = Loan.objects.create(
            member=self.member,
            book_copy=self.book_copy,
            due_at=timezone.now() + timedelta(days=5),
            returned_at=timezone.now(),
            status=Loan.Status.RETURNED
        )

        response = self.client.post("/api/books/return/", {
            "loan_id": loan.id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_return_book_copy_set_to_reserved_if_reservation_exists(self):
        """Test book copy status set to RESERVED when reservation exists"""
        # Create another member to make reservation
        other_user = create_user()
        other_member = Member.objects.get(user=other_user)

        # Create active loan
        loan = Loan.objects.create(
            member=self.member,
            book_copy=self.book_copy,
            due_at=timezone.now() + timedelta(days=5),
            status=Loan.Status.ACTIVE
        )
        self.book_copy.status = BookCopy.Status.BORROWED
        self.book_copy.save()

        # Create a reservation
        Reservation.objects.create(
            member=other_member,
            book=self.book,
            status=Reservation.Status.ACTIVE,
            fulfilled=False,
            expires_at=timezone.now() + timedelta(days=2)
        )

        response = self.client.post("/api/books/return/", {
            "loan_id": loan.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify book copy status is RESERVED
        self.book_copy.refresh_from_db()
        self.assertEqual(self.book_copy.status, BookCopy.Status.RESERVED)

    def test_return_nonexistent_loan(self):
        """Test returning a loan that doesn't exist"""
        response = self.client.post("/api/books/return/", {
            "loan_id": 99999
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_other_member_loan_fails(self):
        """Test member cannot return another member's loan"""
        other_user = create_user()
        other_member = Member.objects.get(user=other_user)

        loan = Loan.objects.create(
            member=other_member,
            book_copy=self.book_copy,
            due_at=timezone.now() + timedelta(days=5),
            status=Loan.Status.ACTIVE
        )

        response = self.client.post("/api/books/return/", {
            "loan_id": loan.id
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_return_requires_authentication(self):
        """Test returning book requires authentication"""
        self.client.force_authenticate(user=None)

        loan = Loan.objects.create(
            member=self.member,
            book_copy=self.book_copy,
            due_at=timezone.now() + timedelta(days=5),
            status=Loan.Status.ACTIVE
        )

        response = self.client.post("/api/books/return/", {
            "loan_id": loan.id
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_return_missing_loan_id_fails(self):
        """Test return without loan_id fails"""
        response = self.client.post("/api/books/return/", {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_updates_returned_at_timestamp(self):
        """Test that returned_at timestamp is set correctly"""
        before_return = timezone.now()
        
        loan = Loan.objects.create(
            member=self.member,
            book_copy=self.book_copy,
            due_at=timezone.now() + timedelta(days=5),
            status=Loan.Status.ACTIVE
        )
        self.book_copy.status = BookCopy.Status.BORROWED
        self.book_copy.save()

        response = self.client.post("/api/books/return/", {
            "loan_id": loan.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        loan.refresh_from_db()
        self.assertIsNotNone(loan.returned_at)
        self.assertGreaterEqual(loan.returned_at, before_return)
