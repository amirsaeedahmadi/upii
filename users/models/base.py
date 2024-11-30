from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import Count
from django.db.models import Q
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from users.exceptions import WrongPasswordError
from users.validators import validate_business_email
from users.validators import validate_mobile
from users.validators import validate_national_code
from users.validators import validate_postal_code
from utils.json import MessageEncoder

ADMIN_PERMISSIONS = {
    "users.view": _("View users"),
    "users.change": _("Add or change users"),
}

ADMIN_GROUPS = {
    "verifications.accountable": _("Accountable for verification requests"),
    "tickets.accountable": _("Accountable for tickets"),
}


class UserManager(DjangoUserManager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("company")

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            msg = "The given email must be set"
            raise ValueError(msg)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            msg = "Superuser must have is_staff=True."
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superuser must have is_superuser=True."
            raise ValueError(msg)

        return self._create_user(email, password, **extra_fields)

    def update_user(self, **kwargs):
        pk = kwargs.pop("id")
        return self.filter(pk=pk).update(**kwargs)

    def get_by_natural_key(self, username):
        # We override this method to make it possible to get user by secondary field
        # if the first one fails.
        try:
            return self.get(**{self.model.USERNAME_FIELD: username})
        except self.model.DoesNotExist:
            return self.get(**{self.model.SECONDARY_USERNAME_FIELD: username})

    def get_assignable_admins(self, filter_kwargs=None, exclude_kwargs=None):
        qs = self.model.objects.filter(
            is_active=True,
            is_staff=True,
            roles__contains=["verifications.accountable"],
        )
        if filter_kwargs:
            qs = qs.filter(**filter_kwargs)
        if exclude_kwargs:
            qs = qs.exclude(**exclude_kwargs)
        return qs

    def get_least_assigned_accountable(self, exclude_kwargs=None):
        from users.models.verification import VerificationRequest

        qs = self.get_assignable_admins(exclude_kwargs=exclude_kwargs)
        return (
            qs.annotate(
                assigned_verification_count=Count(
                    "assigned_verifications",
                    filter=Q(assigned_verifications__status=VerificationRequest.SENT),
                )
            )
            .order_by("assigned_verification_count")
            .first()
        )


def avatar_upload_to(instance, filename):
    return f"users/{instance.pk}/avatar/{filename}"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, editable=False)
    email = models.EmailField(
        unique=True, verbose_name=_("Email"), validators=[validate_business_email]
    )
    email_verified = models.BooleanField(
        default=False, verbose_name=_("Email " "Verified")
    )
    email_verified_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("Email Verified At")
    )
    mobile = models.CharField(
        max_length=16,
        blank=True,
        verbose_name=_("Mobile"),
        validators=[validate_mobile],
    )
    mobile_verified = models.BooleanField(
        default=False, verbose_name=_("Mobile " "Verified")
    )
    mobile_verified_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("Mobile Verified At")
    )
    national_code = models.CharField(
        max_length=16,
        blank=True,
        verbose_name=_("National Code"),
        validators=[validate_national_code],
    )
    shahkar_verified = models.BooleanField(
        default=False, verbose_name=_("Shahkar " "Verified")
    )
    shahkar_verified_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("Shahkar Verified At")
    )
    shahkar_response = models.TextField(
        blank=True, editable=True, verbose_name=_("Shahkar Response Detail")
    )
    postal_code = models.CharField(
        max_length=16,
        blank=True,
        verbose_name=_("Postal " "Code"),
        validators=[validate_postal_code],
    )
    postal_address = models.CharField(
        max_length=256, blank=True, verbose_name=_("Postal Address")
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_to, null=True, verbose_name=_("Avatar")
    )
    avatar_updated_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("Avatar Updated At")
    )
    username = models.CharField(  # noqa: DJ001
        max_length=150,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        null=True,
        verbose_name=_("Username"),
    )
    identity_verified = models.BooleanField(
        default=False, verbose_name=_("Identity " "Verified")
    )
    identity_verified_at = models.DateTimeField(
        null=True, editable=False, verbose_name=_("Identity Verified At")
    )
    identity_verified_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="identity_verifications",
        null=True,
        editable=False,
        verbose_name=_("Identity Verified By"),
    )
    access_list = models.JSONField(default=list, encoder=MessageEncoder)
    roles = models.JSONField(default=list, encoder=MessageEncoder)

    USERNAME_FIELD = "email"
    # Make it possible to get user by username if fails by email.
    SECONDARY_USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return f"{self.email}: {self.pk}"

    @property
    def full_name(self):
        return self.get_full_name()

    @property
    def can_order(self):
        return self.identity_verified

    def reset_password(self, new_password):
        self.set_password(new_password)
        self.save(update_fields=["password"])

    def change_password(self, current_password, new_password):
        if not self.check_password(current_password):
            raise WrongPasswordError
        self.reset_password(new_password)

    def change_username(self, new_username):
        self.username = new_username
        self.save(update_fields=["username"])

    def update_avatar(self, new_avatar):
        self.avatar = new_avatar
        self.avatar_updated_at = timezone.now()
        self.save(update_fields=["avatar", "avatar_updated_at"])

    def delete_avatar(self):
        self.avatar.delete()
        self.avatar_updated_at = timezone.now()
        self.save(update_fields=["avatar", "avatar_updated_at"])

    def update_or_create_company(self, **kwargs):
        from .company import Company

        instance, created = Company.objects.update_or_create(user=self, defaults=kwargs)
        return instance, created


@receiver(post_delete, sender=User)
def delete_avatar_file_after_instance_deleted(sender, instance, **kwargs):
    instance.avatar.delete()
