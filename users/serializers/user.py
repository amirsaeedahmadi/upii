from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.models.base import ADMIN_GROUPS
from users.models.base import ADMIN_PERMISSIONS
from users.models.company import Company
from users.serializers.company import CompanySerializer

User = get_user_model()


class ReadOnlyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = (
            "groups",
            "user_permissions",
        )


class SearchAdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")


class UserSerializer(serializers.ModelSerializer):
    access_list = serializers.MultipleChoiceField(choices=ADMIN_PERMISSIONS)
    roles = serializers.MultipleChoiceField(choices=ADMIN_GROUPS)
    company = serializers.SerializerMethodField()

    def get_company(self, obj):
        if hasattr(obj, "company"):
            return CompanySerializer(obj.company).data
        return CompanySerializer(Company()).data

    class Meta:
        model = User
        exclude = (
            "groups",
            "user_permissions",
        )
        extra_kwargs = {
            "password": {"allow_blank": True, "write_only": True},
        }

    def validate(self, attrs):
        if attrs.get("is_superuser"):
            attrs["is_staff"] = True
            attrs["access_list"] = []
            return attrs

        if "is_staff" in attrs and not attrs["is_staff"]:
            attrs["is_superuser"] = False
            attrs["access_list"] = []
            attrs["roles"] = []

        return attrs

    def validate_access_list(self, value):
        return list(value)

    def validate_roles(self, value):
        return list(value)

    def create(self, validated_data):
        from users.services import user_service

        return user_service.create(**validated_data)

    def update(self, instance, validated_data):
        from users.services import user_service

        return user_service.update(instance, **validated_data)
