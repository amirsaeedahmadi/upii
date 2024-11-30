import magic
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.serializers import ValidationError

from users.exceptions import StatusError
from users.models.company import Company
from users.models.verification import Document
from users.models.verification import VerificationRequest
from users.serializers.me import MeSerializer

User = get_user_model()


class DocumentSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    tp_display = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = "__all__"
        extra_kwargs = {"file": {"write_only": True}}

    def get_filename(self, obj):
        return obj.file.name.split("/")[-1]

    def get_download_url(self, obj):
        return reverse(
            "document-download",
            request=self.context.get("request"),
            kwargs={"pk": obj.pk},
        )

    def get_tp_display(self, obj):
        return Document.TP_CHOICES[obj.tp]

    def validate_file(self, value):
        if value.size > settings.MAX_DOCUMENT_SIZE * 1024 * 1024:
            msg = _("Document file size must be less than {size} MB.")
            raise ValidationError(msg.format(size=settings.MAX_DOCUMENT_SIZE))
        mime_type = magic.from_buffer(value.read(2048), mime=True)
        if mime_type not in ["image/jpg", "image/png", "image/gif", "application/pdf"]:
            msg = _("Documents must be either a picture or PDF.")
            raise ValidationError(msg)
        return value


class AdminVerificationRequestSerializer(serializers.ModelSerializer):
    user = MeSerializer(read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = VerificationRequest
        fields = "__all__"
        depth = 1

    def get_status_display(self, obj):
        return VerificationRequest.STATUS_CHOICES[obj.status]


class VerificationRequestSerializer(AdminVerificationRequestSerializer):
    model = serializers.ChoiceField(write_only=True, choices=["user", "company"])

    class Meta:
        model = VerificationRequest
        exclude = ("accountable", "inspected_at", "accountable_note")
        extra_kwargs = {"accountable_comment": {"read_only": True}}
        depth = 1

    def create(self, validated_data):
        documents = validated_data.pop("documents")
        model = validated_data.pop("model")
        user = self.context["request"].user
        content_object = user if model == "user" else user.company
        with transaction.atomic():
            try:
                instance = VerificationRequest.objects.create_request(
                    model,
                    content_object,
                    status=VerificationRequest.SENT,
                    user=user,
                    **validated_data,
                )
            except IntegrityError as e:
                raise StatusError from e
            for document in documents:
                doc = Document.objects.create(user=user, **document)
                instance.documents.add(doc)

            return instance


class AccountableSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = ("accountable",)
        extra_kwargs = {
            "accountable": {
                "required": True,
                "read_only": False,
                "queryset": User.objects.all(),
            }
        }


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationRequest
        fields = ("status", "accountable_comment")
        extra_kwargs = {
            "status": {"required": True, "read_only": False},
        }

    def validate(self, attrs):
        status = attrs.get("status")
        if status == VerificationRequest.REJECTED:
            if not attrs.get("accountable_comment"):
                msg = _("This field may not be empty, when status is REJECTED.")
                raise ValidationError({"accountable_comment": msg})
        return attrs

    def update(self, instance, validated_data):
        now = timezone.now()
        with transaction.atomic():
            updated = (
                VerificationRequest.objects.filter(pk=instance.pk)
                .exclude(
                    status__in=[
                        VerificationRequest.REJECTED,
                        VerificationRequest.VERIFIED,
                    ]
                )
                .update(inspected_at=now, **validated_data)
            )
            if not updated:
                raise ValidationError({"detail": _("Request already inspected")})
            instance.refresh_from_db()
            if instance.status == VerificationRequest.VERIFIED:
                if instance.content_type.model == "user":
                    updated = User.objects.filter(
                        pk=instance.object_id, identity_verified=False
                    ).update(identity_verified=True, identity_verified_at=now)
                else:
                    updated = Company.objects.filter(
                        pk=instance.object_id, verified=False
                    ).update(verified=True, verified_at=now)
                if not updated:
                    raise ValidationError({"detail": _("User already verified")})
            return instance
