from rest_framework.permissions import SAFE_METHODS
from rest_framework.permissions import BasePermission


class IsAdminHost(BasePermission):
    def has_permission(self, request, view):
        return request.is_admin_host


class IsNotAdminHost(BasePermission):
    def has_permission(self, request, view):
        return not request.is_admin_host


class NotAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_authenticated


class EmailVerified(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.email_verified


class MobileVerified(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.mobile_verified


class ReadOnlyOrEmailVerified(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.method in SAFE_METHODS or request.user.email_verified
        )


class ShahkarVerified(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.shahkar_verified


class CompanyCreated(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return hasattr(user, "company") and user.company.pk is not None


class CEOShahkarVerified(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and request.user.company.ceo_shahkar_verified
        )


class CEOMobileVerified(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and request.user.company.ceo_mobile_verified
        )


class HasAccountableRole(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("verifications.accountable")


class HasViewUsersPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("users.view")


class HasChangeUsersPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("users.change")
