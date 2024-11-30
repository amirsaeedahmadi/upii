from django.conf import settings


def set_cookie(response, key, value="", max_age=None):
    max_age = max_age or settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        secure=settings.SECURED_COOKIE,
        httponly=True,
        samesite="Lax",
    )
