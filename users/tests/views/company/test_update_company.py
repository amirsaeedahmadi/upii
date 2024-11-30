# ruff: noqa: S106
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.models.company import Company
from users.tests.factories import CompanyFactory
from users.tests.factories import UserFactory


class UpdateCompanyTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("company")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(
            email="test@g.com",
            email_verified=True,
            shahkar_verified=True,
            mobile_verified=True,
        )

    def test_unauthenticated(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_email_unverified(self):
        self.user.email_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_shahkar_unverified(self):
        self.user.shahkar_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mobile_unverified(self):
        self.user.mobile_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_company_not_existing(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(Company.objects.filter(user=self.user).first())
        data = response.json()
        self.assertIn("user", data)
        self.assertEqual(data["user"], str(self.user.pk))

    def test_successful(self):
        CompanyFactory(user=self.user)
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("user", data)
        self.assertEqual(data["user"], str(self.user.pk))
