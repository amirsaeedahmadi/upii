from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import NotAuthenticated
from users.serializers.availability import ChangeUsernameSerializer
from users.serializers.availability import CheckAvailabilitySerializer

User = get_user_model()


class CheckAvailabilityView(APIView):
    permission_classes = (NotAuthenticated,)

    def post(self, request):
        serializer = CheckAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exists = User.objects.filter(email=serializer.validated_data["email"]).exists()
        return Response(
            data={"exists": exists},
            status=status.HTTP_200_OK,
        )


class CheckUsernameAvailabilityView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangeUsernameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exists = User.objects.filter(
            username=serializer.validated_data["username"]
        ).exists()
        return Response(
            data={"exists": exists},
            status=status.HTTP_200_OK,
        )


class ChangeUsernameView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangeUsernameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            request.user.change_username(serializer.validated_data["username"])
            return Response(
                _("Username changed successfully."),
                status=status.HTTP_200_OK,
            )
        except IntegrityError as e:
            raise exceptions.ValidationError({"detail": str(e)}) from e
