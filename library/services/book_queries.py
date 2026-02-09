from django.db.models import Count, Q
from library.models.book_models import Book, BookCopy

def base_active_books():
    return Book.objects.filter(is_deleted=False)

def get_available_books(*, title=None, author=None, ordering="title"):
    qs = (
        base_active_books()
        .annotate(
            available_copies=Count(
                "copies",
                filter=Q(copies__status=BookCopy.Status.AVAILABLE)
            )
        )
        .filter(available_copies__gt=0)
        .distinct()
    )

    if title:
        qs = qs.filter(title__icontains=title)

    if author:
        qs = qs.filter(authors__name__icontains=author)

    return qs.order_by(ordering)
