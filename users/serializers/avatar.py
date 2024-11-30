import logging

import magic
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.serializers import ValidationError

logger = logging.getLogger(__name__)

User = get_user_model()


class UpdateAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("avatar",)
        extra_kwargs = {
            "avatar": {"required": True},
        }

    def validate_avatar(self, value):
        if value.size > settings.MAX_AVATAR_SIZE * 1024 * 1024:
            msg = _("Avatar file size must be less than {size} MB.")
            raise ValidationError(msg.format(size=settings.MAX_AVATAR_SIZE))
        mime_type = magic.from_buffer(value.read(2048), mime=True)
        if mime_type not in ["image/jpg", "image/png", "image/gif"]:
            msg = _("Invalid image file.")
            raise ValidationError(msg)
        return value
