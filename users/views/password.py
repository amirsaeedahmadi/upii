from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.exceptions import WrongPasswordError
from users.permissions import NotAuthenticated
from users.serializers.password import ChangePasswordSerializer
from users.serializers.password import RequestResetPasswordSerializer
from users.serializers.password import ResetPasswordSerializer
from users.services import user_service
from utils.tokens import get_otp_expiry
from utils.tokens import get_otp_length
from utils.tokens import verify_email_token_for_user

User = get_user_model()


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            request.user.change_password(**serializer.validated_data)
            return Response(
                _("Password changed successfully."),
                status=status.HTTP_200_OK,
            )
        except WrongPasswordError:
            return Response(
                {"detail": _("Current password is wrong.")},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RequestResetPasswordView(APIView):
    permission_classes = (NotAuthenticated,)

    def post(self, request):
        serializer = RequestResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()
        if user:
            user_service.request_password_reset(user)

        return Response(
            data={
                "email": email,
                "expiry": get_otp_expiry(),
                "length": get_otp_length(),
            },
        )


class ResetPasswordView(APIView):
    permission_classes = (NotAuthenticated,)

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if user and verify_email_token_for_user(
            user,
            serializer.validated_data["code"],
        ):
            user.reset_password(serializer.validated_data["new_password"])
            return Response(
                data={"detail": _("Password changed successfully.")},
                status=status.HTTP_200_OK,
            )

        return Response(
            data={"detail": _("Wrong code or email")},
            status=status.HTTP_400_BAD_REQUEST,
        )
