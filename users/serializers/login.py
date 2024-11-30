import logging

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

logger = logging.getLogger(__name__)

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "national_code",
            "mobile",
        )
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
            "national_code": {"required": True, "allow_blank": False},
            "mobile": {"required": True, "allow_blank": False},
        }


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        if self.context["request"].is_admin_host and not self.user.is_staff:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )
        return validated_data


class VerifyEmailSerializer(serializers.Serializer):
    code = serializers.IntegerField()
