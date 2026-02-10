from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from django.utils import timezone

from library.models.book_models import BookCopy
from library.models.borrow_models import Member, Loan, Fine, Reservation
from factories import create_user, create_book


class BorrowBookAPITests(APITestCase):
    """Tests for the BorrowBookAPI endpoint"""

    def setUp(self):
        """Set up test user, member, and book for each test"""
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.member = Member.objects.get(user=self.user)
        
        self.book = create_book(copies=2)

    def test_member_can_borrow_available_book(self):
        """Test a member can successfully borrow an available book"""
        response = self.client.post("/api/books/borrow/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("loan_id", response.data)
        self.assertIn("due_at", response.data)

        # Verify loan was created
        loan = Loan.objects.get(id=response.data["loan_id"])
        self.assertEqual(loan.member, self.member)
        self.assertEqual(loan.status, Loan.Status.ACTIVE)

        # Verify book copy status changed to BORROWED
        book_copy = loan.book_copy
        self.assertEqual(book_copy.status, BookCopy.Status.BORROWED)

        # Verify due date is 14 days from now
        expected_due = timezone.now() + timedelta(days=14)
        self.assertAlmostEqual(
            (loan.due_at - expected_due).total_seconds(),
            0,
            delta=5  # Allow 5 second difference
        )

    def test_member_can_borrow_multiple_books(self):
        """Test a member can borrow multiple books up to their limit"""
        book1 = create_book(title="Book 1", copies=1)
        book2 = create_book(title="Book 2", copies=1)
        book3 = create_book(title="Book 3", copies=1)

        # Borrow first book
        response1 = self.client.post("/api/books/borrow/", {"book_id": book1.id})
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Borrow second book
        response2 = self.client.post("/api/books/borrow/", {"book_id": book2.id})
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Borrow third book
        response3 = self.client.post("/api/books/borrow/", {"book_id": book3.id})
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)

        # Verify all loans created
        self.assertEqual(Loan.objects.filter(member=self.member).count(), 3)

    def test_member_cannot_borrow_when_no_copies_available(self):
        """Test borrowing fails when no copies are available"""
        # Create a book with only one copy set to BORROWED
        book = create_book(copies=1, copy_status=BookCopy.Status.BORROWED)

        response = self.client.post("/api/books/borrow/", {
            "book_id": book.id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("No available copies", response.data["error"])

    def test_member_cannot_borrow_beyond_limit(self):
        """Test borrowing fails when member reaches borrow limit"""
        # Create 5 different books and borrow them all
        for i in range(5):
            book = create_book(title=f"Book {i}", copies=1)
            response = self.client.post("/api/books/borrow/", {"book_id": book.id})
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try to borrow a 6th book (should fail)
        book6 = create_book(title="Book 6", copies=1)
        response = self.client.post("/api/books/borrow/", {"book_id": book6.id})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Borrow limit reached", response.data["error"])

    def test_inactive_member_cannot_borrow(self):
        """Test that inactive members cannot borrow books"""
        # Deactivate the member
        self.member.is_active = False
        self.member.save()

        response = self.client.post("/api/books/borrow/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Inactive member", response.data["error"])

    def test_member_cannot_borrow_with_outstanding_fines(self):
        """Test member cannot borrow if they have unpaid fines"""
        # Create a paid fine (should not block borrowing)
        book1 = create_book(title="Book 1", copies=1)
        loan1 = Loan.objects.create(
            member=self.member,
            book_copy=book1.copies.first(),
            due_at=timezone.now() - timedelta(days=2)
        )
        Fine.objects.create(loan=loan1, amount=5.00, is_paid=True)

        # Should be able to borrow (fine is paid)
        response = self.client.post("/api/books/borrow/", {
            "book_id": self.book.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create an unpaid fine
        book2 = create_book(title="Book 2", copies=1)
        loan2 = Loan.objects.create(
            member=self.member,
            book_copy=book2.copies.first(),
            due_at=timezone.now() - timedelta(days=2)
        )
        Fine.objects.create(loan=loan2, amount=5.00, is_paid=False)

        # Should not be able to borrow (unpaid fine)
        book3 = create_book(title="Book 3", copies=1)
        response = self.client.post("/api/books/borrow/", {
            "book_id": book3.id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Outstanding fines", response.data["error"])

    def test_member_cannot_borrow_reserved_by_another(self):
        """Test member cannot borrow a book reserved by another member"""
        # Create another member
        other_user = create_user()
        other_member = Member.objects.get(user=other_user)

        # Create a reservation by the other member
        Reservation.objects.create(
            member=other_member,
            book=self.book,
            expires_at=timezone.now() + timedelta(days=2)
        )

        response = self.client.post("/api/books/borrow/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reserved by another member", response.data["error"])

    def test_member_can_borrow_own_reserved_book(self):
        """Test member can borrow a book they have reserved"""
        # Create a reservation by the current member
        reservation = Reservation.objects.create(
            member=self.member,
            book=self.book,
            expires_at=timezone.now() + timedelta(days=2)
        )

        response = self.client.post("/api/books/borrow/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify reservation is marked as fulfilled
        reservation.refresh_from_db()
        self.assertTrue(reservation.fulfilled)
        self.assertEqual(reservation.status, Reservation.Status.FULFILLED)

    def test_borrow_without_authentication_fails(self):
        """Test that unauthenticated requests fail"""
        self.client.force_authenticate(user=None)

        response = self.client.post("/api/books/borrow/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_librarian_cannot_borrow(self):
        """Test that librarians cannot use the borrow endpoint"""
        librarian = create_user(is_librarian=True)
        self.client.force_authenticate(user=librarian)

        response = self.client.post("/api/books/borrow/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_book_id_returns_404(self):
        """Test that borrowing with invalid book_id returns 400"""
        response = self.client.post("/api/books/borrow/", {
            "book_id": 99999
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_book_id_returns_400(self):
        """Test that missing book_id returns validation error"""
        response = self.client.post("/api/books/borrow/", {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_available_copy_is_used(self):
        """Test that only available copies are borrowed, not borrowed ones"""
        # Create book with 2 copies, one available, one borrowed
        book = create_book(copies=2)
        copies = list(book.copies.all())
        copies[0].status = BookCopy.Status.BORROWED
        copies[0].save()

        response = self.client.post("/api/books/borrow/", {
            "book_id": book.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify the available copy was used (not the borrowed one)
        loan = Loan.objects.get(id=response.data["loan_id"])
        self.assertEqual(loan.book_copy, copies[1])


class ReserveBookAPITests(APITestCase):
    """Tests for the ReserveBookAPI endpoint"""

    def setUp(self):
        """Set up test user, member, and book for each test"""
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.member = Member.objects.get(user=self.user)
        
        # Create a book with all copies borrowed so it can be reserved
        self.book = create_book(copies=1, copy_status=BookCopy.Status.BORROWED)

    def test_member_can_reserve_book(self):
        """Test a member can successfully reserve a book"""
        response = self.client.post("/api/books/reserve/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("reservation_id", response.data)
        self.assertIn("expires_at", response.data)

        # Verify reservation was created
        reservation = Reservation.objects.get(id=response.data["reservation_id"])
        self.assertEqual(reservation.member, self.member)
        self.assertEqual(reservation.book, self.book)
        self.assertEqual(reservation.status, Reservation.Status.ACTIVE)

    def test_reservation_expires_in_2_days(self):
        """Test that reservations expire 2 days from creation"""
        response = self.client.post("/api/books/reserve/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        reservation = Reservation.objects.get(id=response.data["reservation_id"])
        expected_expiry = timezone.now() + timedelta(days=2)
        self.assertAlmostEqual(
            (reservation.expires_at - expected_expiry).total_seconds(),
            0,
            delta=5
        )

    def test_member_cannot_reserve_deleted_book(self):
        """Test that members cannot reserve deleted books"""
        from library.models.book_models import Book
        
        # Create and delete a book
        book = create_book(title="Deleted Book")
        book.is_deleted = True
        book.save()

        response = self.client.post("/api/books/reserve/", {
            "book_id": book.id
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_cannot_reserve_twice(self):
        """Test that a member cannot reserve the same book twice"""
        # Create first reservation
        response1 = self.client.post("/api/books/reserve/", {
            "book_id": self.book.id
        })
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Try to create second reservation for same book
        response2 = self.client.post("/api/books/reserve/", {
            "book_id": self.book.id
        })

        # Should fail due to unique constraint
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_multiple_members_can_reserve_same_book(self):
        """Test that multiple different members can reserve the same book"""
        user1 = create_user()
        user2 = create_user()

        # First member reserves
        self.client.force_authenticate(user=user1)
        response1 = self.client.post("/api/books/reserve/", {
            "book_id": self.book.id
        })
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Second member reserves
        self.client.force_authenticate(user=user2)
        response2 = self.client.post("/api/books/reserve/", {
            "book_id": self.book.id
        })
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # Verify both reservations exist
        self.assertEqual(Reservation.objects.filter(book=self.book).count(), 2)

    def test_without_authentication_fails(self):
        """Test that unauthenticated requests fail"""
        self.client.force_authenticate(user=None)

        response = self.client.post("/api/books/reserve/", {
            "book_id": self.book.id
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_book_id_returns_404(self):
        """Test that reserving with invalid book_id returns 404"""
        response = self.client.post("/api/books/reserve/", {
            "book_id": 99999
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CancelReservationAPITests(APITestCase):
    """Tests for the CancelReservationAPI endpoint"""

    def setUp(self):
        """Set up test user, member, and reservation for each test"""
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.member = Member.objects.get(user=self.user)
        
        self.book = create_book(copies=1, copy_status=BookCopy.Status.BORROWED)
        self.reservation = Reservation.objects.create(
            member=self.member,
            book=self.book,
            status=Reservation.Status.ACTIVE,
            expires_at=timezone.now() + timedelta(days=2)
        )

    def test_member_can_cancel_own_reservation(self):
        """Test a member can cancel their own reservation"""
        response = self.client.post("/api/books/cancel-reservation/", {
            "reservation_id": self.reservation.id
        })

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify reservation status changed
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.CANCELLED)

    def test_member_cannot_cancel_others_reservation(self):
        """Test that a member cannot cancel another member's reservation"""
        other_user = create_user()
        self.client.force_authenticate(user=other_user)

        response = self.client.post("/api/books/cancel-reservation/", {
            "reservation_id": self.reservation.id
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_already_cancelled_reservation(self):
        """Test cancelling an already cancelled reservation"""
        self.reservation.status = Reservation.Status.CANCELLED
        self.reservation.save()

        response = self.client.post("/api/books/cancel-reservation/", {
            "reservation_id": self.reservation.id
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_fulfilled_reservation(self):
        """Test cancelling a fulfilled reservation"""
        self.reservation.status = Reservation.Status.FULFILLED
        self.reservation.fulfilled = True
        self.reservation.save()

        response = self.client.post("/api/books/cancel-reservation/", {
            "reservation_id": self.reservation.id
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_reservation_id_returns_404(self):
        """Test that cancelling invalid reservation returns 404"""
        response = self.client.post("/api/books/cancel-reservation/", {
            "reservation_id": 99999
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_without_authentication_fails(self):
        """Test that unauthenticated requests fail"""
        self.client.force_authenticate(user=None)

        response = self.client.post("/api/books/cancel-reservation/", {
            "reservation_id": self.reservation.id
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
