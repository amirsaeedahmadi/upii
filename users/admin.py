from django.contrib import admin
from django.contrib.auth import get_user_model

from .models.admin import SentVerification
from .models.company import Company

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    exclude = ("username",)
    list_display = [
        "full_name",
        "email",
        "is_active",
        "email_verified",
        "identity_verified",
        "is_staff",
        "last_login",
    ]


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "national_code", "user", "verified", "verified_at"]


@admin.register(SentVerification)
class SentVerificationAdmin(admin.ModelAdmin):
    readonly_fields = ("user_comment",)
