import uuid

import factory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from faker import Faker

from users.models.company import Company
from users.models.verification import Document
from users.models.verification import VerificationRequest
from utils.files import uploaded_image_file

User = get_user_model()
faker = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    id = factory.LazyAttribute(lambda _: uuid.uuid4())
    email = factory.LazyAttribute(lambda _: faker.unique.email())
    password = factory.PostGenerationMethodCall(
        "set_password",
        "defaultpassword",
    )
    first_name = factory.LazyAttribute(lambda _: faker.first_name())
    last_name = factory.LazyAttribute(lambda _: faker.last_name())


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    user = factory.SubFactory(UserFactory)


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    user = factory.SubFactory(UserFactory)
    file = uploaded_image_file()
    tp = factory.LazyAttribute(lambda _: faker.random_int(1, 2))


class AbstractVerificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        abstract = True

    user = factory.SubFactory(UserFactory, email_verified=True, shahkar_verified=True)

    @factory.post_generation
    def documents(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return

        # Add the iterable of groups using bulk addition
        self.documents.add(*extracted)


class UserVerificationFactory(AbstractVerificationFactory):
    content_type = ContentType.objects.get(app_label="users", model="user")
    object_id = factory.SelfAttribute("user.pk")

    class Meta:
        model = VerificationRequest


class CompanyVerificationFactory(AbstractVerificationFactory):
    content_type = ContentType.objects.get(app_label="users", model="company")
    company = factory.SubFactory(
        CompanyFactory,
        user=factory.LazyAttribute(lambda o: o.factory_parent.user),
        ceo_shahkar_verified=True,
        ceo_mobile_verified=True,
    )
    object_id = factory.SelfAttribute("company.pk")

    class Meta:
        model = VerificationRequest
        exclude = ["company"]
