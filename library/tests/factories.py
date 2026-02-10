from django.contrib.auth.models import User, Group
from library.models.book_models import Author, Book, BookCopy
from library.models.borrow_models import Member


def create_user(*, is_librarian=False):
    user = User.objects.create_user(
        username=f"user_{User.objects.count()}",
        password="password123"
    )

    group_name = "LIBRARIAN" if is_librarian else "MEMBER"
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)

    # Create Member object for non-librarian users
    if not is_librarian:
        Member.objects.create(
            user=user,
            is_active=True,
            membership_number=f"MEM-{Member.objects.count() + 1:05d}"
        )

    return user


def create_author(name="Author Name"):
    return Author.objects.create(name=name)


def create_book(
    *,
    title="Test Book",
    authors=None,
    copies=1,
    copy_status=BookCopy.Status.AVAILABLE,
):
    if authors is None:
        authors = [create_author()]

    book = Book.objects.create(
        title=title,
        isbn=f"ISBN-{Book.objects.count()}",
        category="Tech",
        description="Some description",
        published_year=2024,
    )
    book.authors.set(authors)

    for i in range(copies):
        BookCopy.objects.create(
            book=book,
            barcode=f"BC-{book.id}-{i}",
            status=copy_status,
            shelf_location="A1"
        )

    return book