from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from utils.models import BaseModel

User = get_user_model()


def upload_doc(instance, filename):
    return f"users/{instance.user.pk}/docs/{filename}"


class Document(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="uploaded_docs", editable=False
    )
    file = models.FileField(upload_to=upload_doc)
    NATIONAL_ID_CARD = 1
    FOUNDED_AD = 2
    TP_CHOICES = {NATIONAL_ID_CARD: _("National ID Card"), FOUNDED_AD: _("Founded Ad")}
    tp = models.PositiveSmallIntegerField(choices=TP_CHOICES)


@receiver(post_delete, sender=Document)
def delete_file_after_instance_deleted(sender, instance, **kwargs):
    instance.file.delete()


class VerificationRequestManager(models.Manager):
    def _create_request(self, app_label, model, object_id, **kwargs):
        content_type = ContentType.objects.get(app_label=app_label, model=model)
        return self.model.objects.create(
            content_type=content_type, object_id=object_id, **kwargs
        )

    def create_request_for_user(self, user_obj, **kwargs):
        return self._create_request("users", "user", user_obj.pk, **kwargs)

    def create_request_for_company(self, company_obj, **kwargs):
        return self._create_request("users", "company", company_obj.pk, **kwargs)

    def create_request(self, model, content_object, **kwargs):
        request = None
        if model == "user":
            request = self.create_request_for_user(content_object, **kwargs)
        elif model == "company":
            request = self.create_request_for_company(content_object, **kwargs)
        return request


class VerificationRequest(BaseModel):
    # "user" or "company"
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, editable=False
    )

    # user id or company id
    object_id = models.CharField(editable=False)

    # user object or company object
    content_object = GenericForeignKey("content_type", "object_id")

    # redundant foreign key to user, to prevent query load
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verification_requests",
        editable=False,
    )
    documents = models.ManyToManyField(Document, verbose_name=_("Documents"))
    SENT = 1
    INSPECTING = 2
    REJECTED = 3
    VERIFIED = 4
    STATUS_CHOICES = {
        SENT: _("Sent"),
        INSPECTING: _("Inspecting"),
        REJECTED: _("Rejected"),
        VERIFIED: _("Verified"),
    }
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=SENT, editable=False, verbose_name=_("Status")
    )

    inspected_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("Inspected at")
    )
    accountable = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_verifications",
        null=True,
        editable=False,
        verbose_name=_("Accountable"),
    )
    accountable_note = models.TextField(
        blank=True,
        help_text=_("This field is not shown to the user"),
        verbose_name=_("Accountable note"),
    )
    accountable_comment = models.TextField(
        blank=True, verbose_name=_("Accountable " "comment")
    )
    user_comment = models.TextField(blank=True, verbose_name=_("User comment"))

    objects = VerificationRequestManager()

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"],
                condition=~Q(status=3),
                name="one_verification_request_at_a_time",
            )
        ]

    def __str__(self):
        return str(self.content_object)

    def assign(self, accountable=None):
        if not accountable:
            exclude_kwargs = {"pk": self.accountable.pk} if self.accountable else {}
            accountable = User.objects.get_least_assigned_accountable(exclude_kwargs)

        if accountable:
            if accountable == self.accountable:
                return None
            if (
                not accountable.is_active
                or not accountable.has_perm("verifications.accountable")
                or not accountable.is_staff
            ):
                return None
            qs = VerificationRequest.objects.filter(pk=self.pk).exclude(
                status__in=[self.REJECTED, self.VERIFIED],
            )
            updated = qs.update(accountable=accountable)

            if updated:
                return accountable
        return None
