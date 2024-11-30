import logging
from datetime import timedelta
from secrets import choice
from string import ascii_uppercase
from string import digits

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_jwt_token_for_user(user):
    from users.serializers.login import LoginSerializer

    return LoginSerializer.get_token(user)


def generate_uppercase_code(length=5):
    return "".join(choice(ascii_uppercase) for i in range(length))


def generate_integer_code(length=5):
    return "".join(choice(digits) for i in range(length))


def get_otp_expiry():
    if isinstance(settings.OTP_EXPIRY, int):
        return settings.OTP_EXPIRY
    elif isinstance(settings.OTP_EXPIRY, timedelta):  # noqa: RET505
        return settings.OTP_EXPIRY.total_seconds()
    return str(settings.OTP_EXPIRY)


def get_otp_length():
    return settings.OTP_LENGTH


def set_email_token_for_user(user):
    length = get_otp_length()
    code = generate_integer_code(length=length)
    expiry = get_otp_expiry()
    cache.set(f"email.verify.token.{user.pk}.{user.email}", code, expiry)
    if settings.LOG_OTPS:
        msg = f"Verification code {code} set for email {user.email}."
        logger.info(msg)
    return code, expiry


def get_email_token_for_user(user):
    return cache.get(f"email.verify.token.{user.pk}.{user.email}")


def verify_email_token_for_user(user, code):
    return get_email_token_for_user(user) == code


def set_mobile_token_for_user(user):
    length = get_otp_length()
    code = generate_integer_code(length=length)
    expiry = get_otp_expiry()
    cache.set(f"mobile.verify.token.{user.pk}.{user.mobile}", code, expiry)
    if settings.LOG_OTPS:
        msg = f"Verification code {code} set for mobile {user.mobile}."
        logger.info(msg)
    return code, expiry


def get_mobile_token_for_user(user):
    return cache.get(f"mobile.verify.token.{user.pk}.{user.mobile}")


def verify_mobile_token_for_user(user, code):
    return get_mobile_token_for_user(user) == code


def set_mobile_token_for_company(company):
    length = get_otp_length()
    code = generate_integer_code(length=length)
    expiry = get_otp_expiry()
    cache.set(f"ceomobile.verify.token.{company.pk}.{company.ceo_mobile}", code, expiry)
    if settings.LOG_OTPS:
        msg = f"Verification code {code} set for mobile {company.ceo_mobile}."
        logger.info(msg)
    return code, expiry


def get_mobile_token_for_company(company):
    return cache.get(f"ceomobile.verify.token.{company.pk}.{company.ceo_mobile}")


def verify_mobile_token_for_company(company, code):
    return get_mobile_token_for_company(company) == code
