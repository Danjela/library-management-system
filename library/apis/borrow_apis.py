from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from library.services.borrowing import borrow_book, BorrowingError
from library.services.returning import return_book
from library.services.reservation import reserve_book
from library.models.book_models import Book
from library.models.borrow_models import Member, Loan, Reservation
from library.serializers.borrow_serializers import BorrowBookSerializer, ReturnBookSerializer
from users.permissions.roles import IsMember
from users.permissions.loan_permissions import IsBorrowerOrLibrarian
from users.permissions.reservation_permissions import IsReservationOwner

class BorrowBookAPI(APIView):
    permission_classes = [IsAuthenticated, IsMember]

    def post(self, request):
        serializer = BorrowBookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = Member.objects.get(user=request.user)
        book = Book.objects.get(id=serializer.validated_data["book_id"])

        try:
            loan = borrow_book(member, book)
        except BorrowingError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "loan_id": loan.id,
                "due_at": loan.due_at
            },
            status=status.HTTP_201_CREATED
        )
    
class ReturnBookAPI(APIView):
    permission_classes = [IsAuthenticated, IsBorrowerOrLibrarian]

    def post(self, request):
        serializer = ReturnBookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = Member.objects.get(user=request.user)
        loan = get_object_or_404(Loan, id=serializer.validated_data["loan_id"], member=member)

        self.check_object_permissions(request, loan)

        try:
            fine_amount = return_book(loan)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                "status": "RETURNED",
                "fine": fine_amount
            },
            status=status.HTTP_201_CREATED
        )

class ReserveBookAPI(APIView):
    permission_classes = [IsAuthenticated, IsMember]

    def post(self, request):

        book = get_object_or_404(
            Book,
            id=request.data["book_id"],
            is_deleted=False
        )

        reservation = reserve_book(
            member=request.user.member,
            book=book
        )

        return Response(
            {
                "reservation_id": reservation.id,
                "expires_at": reservation.expires_at,
            },
            status=201
        )
    
class CancelReservationAPI(APIView):
    permission_classes = [IsAuthenticated, IsReservationOwner]

    def post(self, request):
        self.check_permissions(request)
        
        reservation = get_object_or_404(
            Reservation,
            id=request.data["reservation_id"]
        )

        self.check_object_permissions(request, reservation)

        if reservation.status != Reservation.Status.ACTIVE:
            return Response(
                {"error": f"Cannot cancel a {reservation.status.lower()} reservation"},
                status=status.HTTP_403_FORBIDDEN
            )

        reservation.status = Reservation.Status.CANCELLED
        reservation.save()

        return Response(status=204)

