from django.urls import path

from library.apis.book_apis import (
    BookCreateAPI,
    BookUpdateAPI,
    LibrarianBookDetailAPI,
    MemberBookDetailAPI,
    AvailableBooksAPI,
    BookSoftDeleteAPI,
)

urlpatterns = [

    # ======================
    # PUBLIC ENDPOINTS
    # ======================

    path(
        "public/books/",
        AvailableBooksAPI.as_view(),
        name="member-book-list",
    ),

    # ======================
    # MEMBER ENDPOINTS
    # ======================

    path(
        "public/books/<int:id>/",
        MemberBookDetailAPI.as_view(),
        name="member-book-detail",
    ),

    # ======================
    # LIBRARIAN ENDPOINTS
    # ======================

    path(
        "librarian/books/",
        BookCreateAPI.as_view(),
        name="librarian-book-create",
    ),

    path(
        "librarian/books/<int:id>/",
        LibrarianBookDetailAPI.as_view(),
        name="librarian-book-detail",
    ),

    path(
        "librarian/books/<int:id>/update/",
        BookUpdateAPI.as_view(),
        name="librarian-book-update",
    ),

    path(
        "librarian/books/<int:book_id>/delete/",
        BookSoftDeleteAPI.as_view(),
        name="librarian-book-soft-delete",
    ),
]
