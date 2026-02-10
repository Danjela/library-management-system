from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

class Book(models.Model):
    authors = models.ManyToManyField(Author, related_name="books")

    title = models.CharField(max_length=255, db_index=True)
    isbn = models.CharField(max_length=13, unique=True)
    category = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    published_year = models.IntegerField()
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_deleted"]),
        ]

    def __str__(self):
        return self.title

class BookCopy(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE"
        BORROWED = "BORROWED"
        RESERVED = "RESERVED"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")

    barcode = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    shelf_location = models.CharField(max_length=50)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["book", "status"]),
        ]

