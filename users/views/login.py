import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from users.permissions import IsNotAdminHost
from users.permissions import NotAuthenticated
from users.serializers.login import LoginSerializer
from users.serializers.login import SignupSerializer
from users.serializers.me import MeSerializer
from users.services import user_service
from utils.cookies import set_cookie

logger = logging.getLogger(__name__)
User = get_user_model()


class SignupView(APIView):
    permission_classes = (NotAuthenticated, IsNotAdminHost)

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = user_service.signup(**serializer.validated_data)
        serializer = MeSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = (NotAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        set_cookie(
            response,
            settings.REFRESH_TOKEN_COOKIE_NAME,
            response.data["refresh"],
        )
        del response.data["refresh"]
        set_cookie(
            response,
            settings.ACCESS_TOKEN_COOKIE_NAME,
            response.data["access"],
            max_age=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(),
        )
        response.data["user"] = MeSerializer(serializer.user).data

        return response


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = Response(
            {"detail": _("Logged out successfully.")},
            status=status.HTTP_200_OK,
        )
        for cookie in request.COOKIES:
            response.delete_cookie(cookie)
        return response
