from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from datetime import date
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class LoginSerializer(TokenObtainPairSerializer):
    def get_token(self, user):
        token = super().get_token(user)
        token["roles"] = list(user.groups.values_list("name", flat=True))
        return token

class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value
