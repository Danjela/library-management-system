from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from library.serializers.book_serializers import (
    AvailableBookSerializer, BookCreateSerializer, BookUpdateSerializer,
    MemberBookDetailSerializer, LibrarianBookDetailSerializer
)
from library.services.book_factory import create_book_with_copies
from library.services.book_queries import get_available_books
from library.services.book_updater import update_book_with_copies
from library.services.book_soft_deleter import soft_delete_book
from library.models.book_models import Book
from django.shortcuts import get_object_or_404
from users.permissions.roles import IsMember, IsLibrarian

class BookCreateAPI(CreateAPIView):
    serializer_class = BookCreateSerializer
    permission_classes = [IsAuthenticated, IsLibrarian]

    def perform_create(self, serializer):
        create_book_with_copies(**serializer.validated_data)

class BookUpdateAPI(UpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookUpdateSerializer
    permission_classes = [IsAuthenticated, IsLibrarian]
    lookup_field = 'id'

    def perform_update(self, serializer):
        update_book_with_copies(
            book=serializer.instance,
            data=serializer.validated_data
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        detail_serializer = LibrarianBookDetailSerializer(self.get_object(), context={"request": request})
        return Response(detail_serializer.data)

class LibrarianBookDetailAPI(RetrieveAPIView):
    queryset = Book.objects.prefetch_related("authors", "copies")
    serializer_class = LibrarianBookDetailSerializer
    permission_classes = [IsAuthenticated, IsLibrarian]
    lookup_field = 'id'

class MemberBookDetailAPI(RetrieveAPIView):
    serializer_class = MemberBookDetailSerializer
    permission_classes = [IsAuthenticated, IsMember]
    lookup_field = 'id'

    def get_queryset(self):
        return Book.objects.filter(
            is_deleted=False
        ).prefetch_related("authors")

class BookSoftDeleteAPI(APIView):
    permission_classes = [IsAuthenticated, IsLibrarian]

    def delete(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        soft_delete_book(book=book)
        return Response(status=204)

class AvailableBooksAPI(ListAPIView):
    serializer_class = AvailableBookSerializer
    pagination_class = PageNumberPagination
    ordering_fields = ["title", "published_year"]

    def get_queryset(self):
        return get_available_books(
            title=self.request.query_params.get("title"),
            author=self.request.query_params.get("author"),
            ordering=self.request.query_params.get("ordering", "title"),
        )