import logging

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .company import Company
from .company import CompanySerializer

logger = logging.getLogger(__name__)

User = get_user_model()


class MeSerializer(serializers.ModelSerializer):
    can_order = serializers.BooleanField(read_only=True)
    company = serializers.SerializerMethodField()

    def get_company(self, obj):
        if hasattr(obj, "company"):
            return CompanySerializer(obj.company).data
        return CompanySerializer(Company()).data

    class Meta:
        model = User
        exclude = (
            "password",
            "groups",
            "user_permissions",
        )
        extra_kwargs = {
            "is_active": {
                "read_only": True,
            },
            "is_staff": {
                "read_only": True,
            },
            "is_superuser": {
                "read_only": True,
            },
            "username": {
                "read_only": True,
            },
            "email": {
                "read_only": True,
            },
            "email_verified": {
                "read_only": True,
            },
            "mobile": {
                "read_only": True,
            },
            "mobile_verified": {
                "read_only": True,
            },
            "national_code": {
                "read_only": True,
            },
            "shahkar_verified": {
                "read_only": True,
            },
            "avatar": {
                "read_only": True,
            },
            "identity_verified": {
                "read_only": True,
            },
        }


class VerifyEmailSerializer(serializers.Serializer):
    code = serializers.CharField()


class EmailVerifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email_verified", "email_verified_at")


class VerifyShahkarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("national_code", "mobile")
        extra_kwargs = {
            "national_code": {"required": True},
            "mobile": {"required": True},
        }


class ShahkarVerifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "shahkar_verified", "shahkar_verified_at", "shahkar_response")


class VerifyMobileSerializer(serializers.Serializer):
    code = serializers.CharField()


class MobileVerifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "mobile_verified", "mobile_verified_at")
