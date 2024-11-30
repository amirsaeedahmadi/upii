from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.validators import validate_mobile
from users.validators import validate_national_code
from users.validators import validate_phone
from users.validators import validate_postal_code
from utils.models import BaseModel

User = get_user_model()


class Company(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="company",
        editable=False,
        verbose_name=_("User"),
    )
    name = models.CharField(max_length=128, blank=True, verbose_name=_("Name"))
    national_code = models.CharField(
        max_length=128, blank=True, verbose_name=_("National Code")
    )
    registry_code = models.CharField(
        max_length=128, blank=True, verbose_name=_("Registry Code")
    )
    economical_number = models.CharField(
        max_length=128, blank=True, verbose_name=_("Eco. Number")
    )
    phone = models.CharField(
        max_length=128, blank=True, verbose_name=_("Phone"), validators=[validate_phone]
    )
    postal_code = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_("Postal " "Code"),
        validators=[validate_postal_code],
    )
    postal_address = models.CharField(
        max_length=128, blank=True, verbose_name=_("Postal Address")
    )
    size = models.PositiveSmallIntegerField(null=True, verbose_name=_("Size"))
    activity_field = models.CharField(
        max_length=128, blank=True, verbose_name=_("Activity Field")
    )
    ceo_mobile = models.CharField(
        max_length=16,
        blank=True,
        verbose_name=_("CEO " "Mobile"),
        validators=[validate_mobile],
    )
    ceo_mobile_verified = models.BooleanField(
        default=False, verbose_name=_("CEO " "Mobile " "Verified")
    )
    ceo_mobile_verified_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("CEO Mobile Verified At")
    )
    ceo_national_code = models.CharField(
        max_length=16,
        blank=True,
        verbose_name=_("CEO National Code"),
        validators=[validate_national_code],
    )
    ceo_shahkar_verified = models.BooleanField(
        default=False, verbose_name=_("CEO Shahkar Verified")
    )
    ceo_shahkar_verified_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("CEO Shahkar Verified At")
    )
    ceo_shahkar_response = models.TextField(
        blank=True, editable=True, verbose_name=_("CEO Shahkar Response")
    )
    verified = models.BooleanField(
        default=False, editable=False, verbose_name=_("Verified")
    )
    verified_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("Verified At")
    )

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
