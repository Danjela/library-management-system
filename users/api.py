from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from users.serializers import LoginSerializer, RegisterSerializer
from users.services.register_member import register_member


class RegisterAPI(APIView):

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        register_member(data=serializer.validated_data)

        return Response(
            {"message": "Registration successful. Verify your email."},
            status=status.HTTP_201_CREATED
        )

class LoginAPI(TokenObtainPairView):

    serializer_class = LoginSerializer

class LogoutAPI(APIView):

    def post(self, request):
        RefreshToken(request.data["refresh"]).blacklist()
        return Response(status=204)
