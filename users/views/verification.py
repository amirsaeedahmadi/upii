import mimetypes

from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.events import UserUpdated
from users.events import VerificationAssigned
from users.events import VerificationCreated
from users.events import VerificationInspected
from users.exceptions import StatusError
from users.models.verification import Document
from users.models.verification import VerificationRequest
from users.permissions import CEOMobileVerified
from users.permissions import CEOShahkarVerified
from users.permissions import CompanyCreated
from users.permissions import EmailVerified
from users.permissions import HasAccountableRole
from users.permissions import IsAdminHost
from users.permissions import IsNotAdminHost
from users.permissions import ShahkarVerified
from users.serializers.me import MeSerializer
from users.serializers.user import SearchAdminUserSerializer
from users.serializers.verification import AccountableSerializer
from users.serializers.verification import AdminVerificationRequestSerializer
from users.serializers.verification import DocumentSerializer
from users.serializers.verification import InspectionSerializer
from users.serializers.verification import VerificationRequestSerializer
from users.services import kafka_event_store

User = get_user_model()


class VerificationRequestViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = VerificationRequest.objects.all()
    filterset_fields = ("content_type__model", "status", "accountable", "user")
    order_fields = ("created_at",)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"] and self.request.is_admin_host:
            return AdminVerificationRequestSerializer

        if self.action == "assignables":
            return SearchAdminUserSerializer

        if self.action == "assign":
            return AccountableSerializer

        if self.action == "inspect":
            return InspectionSerializer

        return VerificationRequestSerializer

    def get_permission_classes(self):
        if self.action == "list":
            if self.request.is_admin_host:
                return [HasAccountableRole]
            return [EmailVerified]

        if self.action == "create":
            perms = [IsNotAdminHost, EmailVerified]
            serializer = self.get_serializer(data=self.request.data)
            serializer.is_valid(raise_exception=True)
            if serializer.validated_data["model"] == "user":
                perms.extend([ShahkarVerified])
            else:
                perms.extend([CompanyCreated, CEOShahkarVerified, CEOMobileVerified])
            return perms

        if self.action in ["retrieve", "assignables", "assign", "inspect"]:
            return [IsAdminHost, HasAccountableRole]

        return []

    def get_permissions(self):
        return [permission() for permission in self.get_permission_classes()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.is_admin_host:
            if self.request.user.is_superuser:
                return qs
            return qs.filter(accountable=self.request.user)
        return qs.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        documents = []
        for key, value in request.FILES.items():
            data = {"file": value, "tp": key}
            serializer = DocumentSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            documents.append(data)

        if not documents:
            return Response(
                data={"detail": _("No documents.")}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance = serializer.save(documents=documents)
            event = VerificationCreated(
                AdminVerificationRequestSerializer(instance).data
            )
            kafka_event_store.add_event(event)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        except StatusError:
            return Response(
                data={"detail": _("Status Error")}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=["GET"], detail=True)
    def assignables(self, request, pk=None):
        instance = self.get_object()
        exclude_kwargs = {"pk": instance.accountable.pk} if instance.accountable else {}
        search = request.GET.get("search")
        if not search:
            raise ValidationError({"search": _("This url param is required.")})
        queryset = User.objects.get_assignable_admins(
            filter_kwargs={"email__contains": search}, exclude_kwargs=exclude_kwargs
        ).order_by("email")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=["PATCH"], detail=True)
    def assign(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        accountable = instance.assign(**serializer.validated_data)
        if accountable:
            instance.refresh_from_db()
            serializer = AdminVerificationRequestSerializer(instance)
            event = VerificationAssigned(serializer.data)
            kafka_event_store.add_event(event)
            return Response(serializer.data)

        return Response(
            {
                "detail": _(
                    "No one new was assigned. "
                    "This may be because no accountable "
                    "exists, or the request is already rejected or verified. "
                    "And also make sure you are not already accountable to "
                    "this request."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(methods=["PATCH"], detail=True)
    def inspect(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = AdminVerificationRequestSerializer(instance)
        event = VerificationInspected(serializer.data)
        kafka_event_store.add_event(event)
        if instance.status == VerificationRequest.VERIFIED:
            event = UserUpdated(MeSerializer(instance.user).data)
            kafka_event_store.add_event(event)
        return Response(serializer.data)


class DownloadDocumentView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk=None):
        obj = Document.objects.filter(pk=pk).first()
        if obj:
            if request.is_admin_host:
                if not request.user.has_perm("verifications.accountable"):
                    raise NotFound
            elif request.user != obj.user:
                raise NotFound

            try:
                with open(obj.file.path, "rb") as file:  # noqa: PTH123
                    content_type, encoding = mimetypes.guess_type(obj.file.path)
                    return HttpResponse(file.read(), content_type=content_type)
            except FileNotFoundError as e:
                msg = _("File not found. It may have been deleted")
                raise NotFound(msg) from e

        raise NotFound
