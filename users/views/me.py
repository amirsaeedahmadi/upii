from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users import services
from users.exceptions import EmailVerificationError
from users.exceptions import MobileVerificationError
from users.permissions import EmailVerified
from users.permissions import ShahkarVerified
from users.serializers.me import EmailVerifiedSerializer
from users.serializers.me import MeSerializer
from users.serializers.me import MobileVerifiedSerializer
from users.serializers.me import ShahkarVerifiedSerializer
from users.serializers.me import VerifyEmailSerializer
from users.serializers.me import VerifyMobileSerializer
from users.serializers.me import VerifyShahkarSerializer
from users.services import user_service
from users.throttles import OTPRateThrottle
from utils import tokens

User = get_user_model()


class CheckStatusView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        if request.user.is_authenticated:
            serializer = MeSerializer(request.user, context={"request": request})
            return Response({"user": serializer.data})
        return Response({"user": None})


class MeView(APIView):
    def get(self, request):
        try:
            instance = User.objects.get(email=request.user.email)
        except User.DoesNotExist as e:
            raise NotFound(_("User does not exist.")) from e

        serializer = MeSerializer(instance)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        instance = request.user
        serializer = MeSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        instance = user_service.update(instance, **serializer.validated_data)
        return Response(
            MeSerializer(instance).data,
            status=status.HTTP_200_OK,
        )


class RequestVerifyEmailView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        if request.user.email_verified:
            detail = _('Email address "{email}" is already verified.')
            return Response(
                data={"detail": detail.format(email=request.user.email)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_service.request_email_verification(request.user)
        return Response(
            data={
                "email": request.user.email,
                "expiry": tokens.get_otp_expiry(),
                "length": tokens.get_otp_length(),
            },
        )


class VerifyEmailView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if request.user.email_verified:
            detail = _('Email address "{email}" is already verified.')
            return Response(
                data={"detail": detail.format(email=request.user.email)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = user_service.verify_email(
                request.user,
                serializer.validated_data["code"],
            )
        except EmailVerificationError:
            return Response(
                data={"detail": _("Wrong code.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            serializer = EmailVerifiedSerializer(instance)
            return Response(data=serializer.data, status=status.HTTP_200_OK)


class VerifyShahkarView(APIView):
    def post(self, request):
        if request.user.shahkar_verified:
            detail = _('Shahkar for "{code}" on "{mobile}" is already verified.')
            detail = detail.format(
                code=request.user.national_code,
                mobile=request.user.mobile,
            )
            return Response(
                data={"detail": detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = VerifyShahkarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = user_service.update_national_code_and_mobile(
                request.user,
                serializer.validated_data["national_code"],
                serializer.validated_data["mobile"],
            )
        except services.ShahkarVerificationError as e:
            return Response(data={"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = ShahkarVerifiedSerializer(instance)
            return Response(data=serializer.data, status=status.HTTP_200_OK)


class RequestVerifyMobileView(APIView):
    permission_classes = (IsAuthenticated, EmailVerified, ShahkarVerified)

    def post(self, request):
        if request.user.mobile_verified:
            detail = _('Mobile number "{mobile}" is already verified.')
            return Response(
                data={"detail": detail.format(mobile=request.user.mobile)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_service.request_mobile_verification(request.user)
        return Response(
            data={
                "mobile": request.user.mobile,
                "expiry": tokens.get_otp_expiry(),
                "length": tokens.get_otp_length(),
            },
        )


class VerifyMobileView(APIView):
    permission_classes = (IsAuthenticated, EmailVerified, ShahkarVerified)

    def post(self, request):
        if request.user.mobile_verified:
            detail = _('Mobile number "{mobile}" is already verified.')
            return Response(
                data={"detail": detail.format(mobile=request.user.mobile)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = VerifyMobileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = user_service.verify_mobile(
                request.user,
                serializer.validated_data["code"],
            )
        except MobileVerificationError:
            return Response(
                data={"detail": _("Wrong code.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            serializer = MobileVerifiedSerializer(instance)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
