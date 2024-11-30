from django.contrib.auth import get_user_model
from django.test import TestCase

from users.models.verification import VerificationRequest
from users.tests.factories import UserFactory
from users.tests.factories import UserVerificationFactory

User = get_user_model()


class AssignVerificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        UserFactory.create_batch(2, is_staff=True, roles=["verifications.accountable"])
        cls.staff1 = User.objects.first()
        cls.staff2 = User.objects.last()
        UserVerificationFactory.create_batch(3)

    def test_load_balancing(self):
        vr = VerificationRequest.objects.first()
        vr.accountable = self.staff1
        vr.save()
        vr = VerificationRequest.objects.last()
        self.assertEqual(vr.assign(), self.staff2)
