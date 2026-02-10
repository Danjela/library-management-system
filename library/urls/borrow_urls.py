from django.urls import path

from library.apis.borrow_apis import (
    BorrowBookAPI,
    ReturnBookAPI,
    ReserveBookAPI,
    CancelReservationAPI,
)

urlpatterns = [
    # -----------------------------
    # Borrowing
    # -----------------------------
    path(
        "books/borrow/",
        BorrowBookAPI.as_view(),
        name="book-borrow"
    ),
    path(
        "books/return/",
        ReturnBookAPI.as_view(),
        name="book-return"
    ),

    # -----------------------------
    # Reservations
    # -----------------------------
    path(
        "books/reserve/",
        ReserveBookAPI.as_view(),
        name="book-reserve"
    ),
    path(
        "books/cancel-reservation/",
        CancelReservationAPI.as_view(),
        name="reservation-cancel"
    ),
]
