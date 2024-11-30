from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models.verification import VerificationRequest


class VerificationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=VerificationRequest.SENT)


class SentVerification(VerificationRequest):
    objects = VerificationManager()

    class Meta:
        proxy = True
        verbose_name = _("Pending Verification Request")
        verbose_name_plural = _("Pending Verification Requests")
