from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from library.models.book_models import BookCopy

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    membership_number = models.CharField(max_length=20, unique=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_books_allowed = models.PositiveIntegerField(default=5)

class Loan(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        RETURNED = "RETURNED"
        OVERDUE = "OVERDUE"

    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE)

    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["book_copy"],
                condition=Q(status="ACTIVE"),
                name="one_active_loan_per_copy"
            )
        ]

class Reservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        FULFILLED = "FULFILLED"
        CANCELLED = "CANCELLED"
        EXPIRED = "EXPIRED"

    member = models.ForeignKey(
        "library.Member",
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    book = models.ForeignKey(
        "library.Book",
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    fulfilled = models.BooleanField(default=False)

    class Meta:
        unique_together = ["member", "book"]
        indexes = [
            models.Index(fields=["book", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    @staticmethod
    def default_expiry():
        return now() + timedelta(days=2)

class Fine(models.Model):
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=6, decimal_places=2)
    currency = models.CharField(max_length=10, default="EUR")
    is_paid = models.BooleanField(default=False)
