import logging

from rest_framework import serializers

from users.models.company import Company

logger = logging.getLogger(__name__)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class VerifyCEOShahkarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("ceo_mobile", "ceo_national_code")
        extra_kwargs = {
            "ceo_national_code": {"required": True},
            "ceo_mobile": {"required": True},
        }


class VerifyCEOMobileSerializer(serializers.Serializer):
    code = serializers.CharField()
