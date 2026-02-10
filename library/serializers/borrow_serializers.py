from rest_framework import serializers
from library.models.book_models import Book
from library.models.borrow_models import Loan


class BorrowBookSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()

    def validate_book_id(self, value):
        if not Book.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError("Book not found")
        return value
    
class ReturnBookSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField()

    def validate_loan_id(self, value):
        if not Loan.objects.filter(id=value).exists():
            raise serializers.ValidationError("Loan not found")
        return value
