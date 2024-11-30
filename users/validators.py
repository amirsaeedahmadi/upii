# ruff: noqa: PLR2004
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

EMAIL_DOMAIN_BLACKLIST = {
    "aol.com",
    "apple.com",
    "gmail.com",
    "hotmail.com",
    "icloud.com",
    "mail.com",
    "outlook.com",
    "yahoo.com",
}


def validate_business_email(email):
    validate_email(email)
    domain = email.split("@")[-1].lower()
    if domain in EMAIL_DOMAIN_BLACKLIST:
        raise ValidationError(
            _("Enter a valid business email address."),
            code="invalid",
            params={"value": email},
        )


def validate_mobile(mobile, *, strict=False):
    if len(mobile) > 12 or len(mobile) < 10:
        raise ValidationError(
            _("Invalid mobile number"), code="invalid", params={"value": mobile}
        )
    if not mobile.isdigit():
        if not (mobile[0] == "+" and mobile[1:].isdigit()):
            raise ValidationError(
                _("Invalid mobile number"), code="invalid", params={"value": mobile}
            )
    if strict:
        if not mobile.startswith("09"):
            raise ValidationError(
                _("Invalid mobile number"), code="invalid", params={"value": mobile}
            )


def validate_phone(phone, code=None):
    if code and not phone.startswith(code):
        raise ValidationError(
            _("Invalid phone number"), code="invalid", params={"value": phone}
        )
    if phone.startswith(("09", "9")):
        raise ValidationError(
            _("Invalid phone number"), code="invalid", params={"value": phone}
        )
    if len(phone) != 11:
        raise ValidationError(
            _("Invalid phone number"), code="invalid", params={"value": phone}
        )


def validate_national_code(ncode):
    ncode = str(ncode)
    if not re.match(r"[0-9]{10}", ncode):
        raise ValidationError(
            _("Invalid national code"), code="invalid", params={"value": ncode}
        )
    total = 0
    for i, c in enumerate(ncode[:9]):
        try:
            a = int(c)
        except Exception as e:
            raise ValidationError(
                _("Invalid national code"), code="invalid", params={"value": ncode}
            ) from e
        total += a * (10 - i)
    if not total:
        raise ValidationError(
            _("Invalid national code"), code="invalid", params={"value": ncode}
        )
    r = total % 11
    ctrl_digit = r if r < 2 else 11 - r
    if int(ncode[9]) != ctrl_digit:
        raise ValidationError(
            _("Invalid national code"), code="invalid", params={"value": ncode}
        )


def validate_postal_code(code):
    if len(code) != 10:
        raise ValidationError(
            _("Invalid postal code"), code="invalid", params={"value": code}
        )
