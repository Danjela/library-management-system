from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from library.serializers.book_serializers import AvailableBookSerializer, BookCreateSerializer, BookUpdateSerializer, MemberBookDetailSerializer, LibrarianBookDetailSerializer
from library.services.book_factory import create_book_with_copies
from library.services.book_queries import get_available_books
from library.services.book_updater import update_book_with_copies
from library.services.book_soft_deleter import soft_delete_book
from library.models.book_models import Book
from django.shortcuts import get_object_or_404
from users.permissions.roles import IsMember, IsLibrarian

class BookCreateAPI(APIView):
    permission_classes = [IsAuthenticated, IsLibrarian]

    def post(self, request):
        serializer = BookCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = create_book_with_copies(**serializer.validated_data)

        return Response({"id": book.id}, status=201)
    
class BookUpdateAPI(APIView):
    permission_classes = [IsAuthenticated, IsLibrarian]

    def put(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)

        serializer = BookUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_book_with_copies(
            book=book,
            data=serializer.validated_data
        )

        return Response(status=204)
    
class LibrarianBookDetailAPI(APIView):
    permission_classes = [IsAuthenticated, IsLibrarian]

    def get(self, request, book_id):
        book = get_object_or_404(
            Book.objects.prefetch_related("authors", "copies"),
            id=book_id
        )
        serializer = LibrarianBookDetailSerializer(book)
        return Response(serializer.data)

class MemberBookDetailAPI(APIView):
    permission_classes = [IsAuthenticated, IsMember]

    def get(self, request, book_id):
        book = get_object_or_404(
            Book.objects.filter(is_deleted=False).prefetch_related("authors"),
            id=book_id
        )
        serializer = MemberBookDetailSerializer(book)
        return Response(serializer.data)

class BookSoftDeleteAPI(APIView):
    permission_classes = [IsAuthenticated, IsLibrarian]

    def delete(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        soft_delete_book(book=book)
        return Response(status=204)

    
class AvailableBooksAPI(ListAPIView):
    serializer_class = AvailableBookSerializer
    ordering_fields = ["title", "published_year"]

    def get_queryset(self):
        return get_available_books(
            title=self.request.query_params.get("title"),
            author=self.request.query_params.get("author"),
            ordering=self.request.query_params.get("ordering", "title"),
        )
