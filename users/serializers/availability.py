import logging

from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.validators import validate_business_email

logger = logging.getLogger(__name__)

User = get_user_model()


class CheckAvailabilitySerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[validate_business_email])


class ChangeUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username",)
        extra_kwargs = {
            "username": {"required": True},
        }
