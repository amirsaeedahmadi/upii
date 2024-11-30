from django.urls import path
from rest_framework.routers import SimpleRouter

from users.views.users import UserViewSet

from .views.availability import ChangeUsernameView
from .views.availability import CheckAvailabilityView
from .views.availability import CheckUsernameAvailabilityView
from .views.avatar import AvatarView
from .views.company import CompanyView
from .views.company import CompanyViewSet
from .views.login import LoginView
from .views.login import LogoutView
from .views.login import SignupView
from .views.me import CheckStatusView
from .views.me import MeView
from .views.me import RequestVerifyEmailView
from .views.me import RequestVerifyMobileView
from .views.me import VerifyEmailView
from .views.me import VerifyMobileView
from .views.me import VerifyShahkarView
from .views.password import ChangePasswordView
from .views.password import RequestResetPasswordView
from .views.password import ResetPasswordView
from .views.permissions import AccessListView
from .views.permissions import RoleListView
from .views.verification import DownloadDocumentView
from .views.verification import VerificationRequestViewSet

# User Endpoints
urlpatterns = [
    path("status/", CheckStatusView.as_view(), name="check-status"),
    path(
        "checkavailability/", CheckAvailabilityView.as_view(), name="check-availability"
    ),
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("changepassword/", ChangePasswordView.as_view(), name="change-password"),
    path(
        "resetpassword/request/",
        RequestResetPasswordView.as_view(),
        name="request-reset-password",
    ),
    path("resetpassword/", ResetPasswordView.as_view(), name="reset-password"),
    path("me/", MeView.as_view(), name="me"),
    path(
        "checkusername/", CheckUsernameAvailabilityView.as_view(), name="check-username"
    ),
    path("changeusername/", ChangeUsernameView.as_view(), name="change-username"),
    path("avatar/", AvatarView.as_view(), name="avatar"),
    path(
        "email/request/verify/",
        RequestVerifyEmailView.as_view(),
        name="request-verify-email",
    ),
    path("email/verify/", VerifyEmailView.as_view(), name="verify-email"),
    path("shahkar/verify/", VerifyShahkarView.as_view(), name="verify-shahkar"),
    path(
        "mobile/request/verify/",
        RequestVerifyMobileView.as_view(),
        name="request-verify-mobile",
    ),
    path(
        "mobile/verify/",
        VerifyMobileView.as_view(),
        name="verify-mobile",
    ),
    path("company/", CompanyView.as_view(), name="company"),
    path(
        "documents/<pk>/download/",
        DownloadDocumentView.as_view(),
        name="document-download",
    ),
    path(
        "accesslist/",
        AccessListView.as_view(),
        name="access-list",
    ),
    path(
        "roles/",
        RoleListView.as_view(),
        name="role-list",
    ),
]


router = SimpleRouter()
router.register(r"companies", CompanyViewSet)
router.register(r"verifications", VerificationRequestViewSet)
router.register(r"", UserViewSet)

urlpatterns += router.urls
