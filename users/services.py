# ruff: noqa: FBT002, PLR0913
import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import IntegrityError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from utils import tokens
from utils.decorators import delay_return
from utils.kafka import KafkaEventStore

from .events import EmailVerificationRequested
from .events import MobileVerificationRequested
from .events import PasswordResetRequested
from .events import UserCreated
from .events import UserDeleted
from .events import UserUpdated
from .exceptions import EmailVerificationError
from .exceptions import MobileVerificationError
from .serializers.user import ReadOnlyUserSerializer
from .shahkar import ShahkarVerificationError
from .shahkar import shahkar

logger = logging.getLogger(__name__)
User = get_user_model()
bootstrap_servers = settings.KAFKA_URL
kafka_event_store = KafkaEventStore(bootstrap_servers=bootstrap_servers)


class UserService:
    def __init__(self, event_store):
        self.event_store = event_store

    @delay_return()
    def create(self, **kwargs):
        email = kwargs.pop("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError({"detail": _("User already exists.")})
        pk = uuid.uuid4()
        password = kwargs.pop("password", None)
        if password:
            password = make_password(password)
        instance = User(pk=pk, email=email, password=password, **kwargs)
        serializer = ReadOnlyUserSerializer(instance)
        event = UserCreated(serializer.data)
        self.event_store.add_event(event)
        return instance

    @staticmethod
    def on_user_created(**kwargs):
        try:
            User.objects.create(**kwargs)
        except IntegrityError as e:
            msg = f"IntegrityError: {kwargs['email']} - {e!s}"
            logger.warning(msg)

    def signup(self, email, password, first_name, last_name, national_code, mobile):
        if User.objects.filter(email=email).exists():
            raise ValidationError({"detail": _("User already exists.")})
        verified, res = shahkar.verify(national_code, mobile)
        if not verified:
            raise ValidationError(res.data)
        return self.create(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            national_code=national_code,
            mobile=mobile,
            shahkar_verified=True,
            shahkar_verified_at=timezone.now(),
            shahkar_response=res.text,
        )

    @delay_return()
    def update(self, instance, **kwargs):
        if "password" in kwargs:
            kwargs["password"] = make_password(kwargs["password"])
        for key, value in kwargs.items():
            setattr(instance, key, value)
        serializer = ReadOnlyUserSerializer(instance)
        event = UserUpdated(serializer.data)
        self.event_store.add_event(event)
        return instance

    def delete(self, instance):
        event = UserDeleted({"id": str(instance.pk)})
        self.event_store.add_event(event)

    def update_national_code_and_mobile(self, instance, national_code, mobile):
        verified, res = shahkar.verify(national_code, mobile)
        if not verified:
            raise ValidationError(res.data)
        if verified:
            return self.update(
                instance,
                national_code=national_code,
                mobile=mobile,
                shahkar_verified=True,
                shahkar_verified_at=timezone.now(),
                shahkar_response=res.text,
            )
        raise ShahkarVerificationError(res.text)

    def request_email_verification(self, instance):
        code, expiry = tokens.set_email_token_for_user(instance)
        payload = {
            "id": str(instance.pk),
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "verification_code": code,
            "expires_in_minutes": expiry,
        }
        event = EmailVerificationRequested(payload)
        self.event_store.add_event(event)

    def verify_email(self, instance, code):
        if tokens.verify_email_token_for_user(instance, code):
            instance = self.update(
                instance, email_verified=True, email_verified_at=timezone.now()
            )
            cache.delete(f"email.verify.token.{instance.pk}.{instance.email}")
            return instance
        raise EmailVerificationError

    def request_mobile_verification(self, instance):
        code, expiry = tokens.set_mobile_token_for_user(instance)
        payload = {
            "id": str(instance.pk),
            "mobile": instance.mobile,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "verification_code": code,
            "expires_in_minutes": expiry,
        }
        event = MobileVerificationRequested(payload)
        self.event_store.add_event(event)

    def verify_mobile(self, instance, code):
        if tokens.verify_mobile_token_for_user(instance, code):
            instance = self.update(
                instance, mobile_verified=True, mobile_verified_at=timezone.now()
            )
            cache.delete(f"mobile.verify.token.{instance.pk}.{instance.mobile}")
            return instance
        raise MobileVerificationError

    def request_password_reset(self, instance):
        code, expiry = tokens.set_email_token_for_user(instance)
        payload = {
            "id": str(instance.pk),
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "verification_code": code,
            "expires_in_minutes": expiry,
        }
        event = PasswordResetRequested(payload)
        self.event_store.add_event(event)


user_service = UserService(kafka_event_store)
