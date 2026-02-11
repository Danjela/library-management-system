from rest_framework import serializers
from library.models.book_models import Book, BookCopy

class BookCopyInputSerializer(serializers.Serializer):
    barcode = serializers.CharField(max_length=50)
    shelf_location = serializers.CharField(max_length=50)

class BookCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    isbn = serializers.CharField()
    category = serializers.CharField()
    description = serializers.CharField()
    published_year = serializers.IntegerField()
    authors = serializers.ListField(child=serializers.CharField())
    copies = BookCopyInputSerializer(many=True)

class BookCopyUpdateSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    barcode = serializers.CharField(max_length=50, required=False)
    shelf_location = serializers.CharField(max_length=50, required=False)

class BookUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    published_year = serializers.IntegerField(required=False)
    authors = serializers.ListField(child=serializers.CharField(), required=False)
    copies = BookCopyUpdateSerializer(many=True, required=False)

class BookCopyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = ["id", "barcode", "status", "shelf_location"]

class LibrarianBookDetailSerializer(serializers.ModelSerializer):
    authors = serializers.StringRelatedField(many=True)
    copies = BookCopyDetailSerializer(many=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "authors",
            "category",
            "description",
            "published_year",
            "is_deleted",
            "copies",
        ]

class MemberBookDetailSerializer(serializers.ModelSerializer):
    authors = serializers.StringRelatedField(many=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "authors",
            "category",
            "description",
            "published_year",
        ]

class AvailableBookSerializer(serializers.ModelSerializer):
    authors = serializers.StringRelatedField(many=True)
    available_copies = serializers.IntegerField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "authors",
            "category",
            "description",
            "published_year",
            "available_copies",
        ]