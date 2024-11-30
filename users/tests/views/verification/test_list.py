from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.models.verification import VerificationRequest
from users.tests.factories import CompanyFactory
from users.tests.factories import CompanyVerificationFactory
from users.tests.factories import UserFactory
from users.tests.factories import UserVerificationFactory


class ListVerificationRequestsTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("verificationrequest-list")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(
            email="user@g.com",
            email_verified=True,
            shahkar_verified=True,
            mobile_verified=True,
        )
        cls.company = CompanyFactory(user=cls.user)
        cls.staff = UserFactory(
            email="admin@admin.com", is_staff=True, roles=["verifications.accountable"]
        )
        cls.superuser = UserFactory(email="super@admin.com", is_superuser=True)
        UserVerificationFactory.create_batch(2, accountable=cls.staff)
        UserVerificationFactory(user=cls.user)
        UserVerificationFactory.create_batch(14)
        CompanyVerificationFactory.create_batch(3, accountable=cls.staff)
        CompanyVerificationFactory(user=cls.user, company=cls.company)
        CompanyVerificationFactory(
            user=cls.user, company=cls.company, status=VerificationRequest.REJECTED
        )
        CompanyVerificationFactory.create_batch(14)

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_superuser_on_admin_host(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertEqual(data["count"], 36)
        result = results[0]
        self.assertIn("accountable", result)
        self.assertIn("documents", result)

    def test_filter_by_accountable(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get(
            self.url,
            {"accountable": self.staff.pk},
            headers={"host": "api.admin.testserver"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertEqual(len(results), 5)
        result = results[0]
        self.assertIn("accountable", result)
        self.assertIn("documents", result)

    def test_accountable_queryset_on_admin_host(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertEqual(len(results), 5)
        result = results[0]
        self.assertIn("accountable", result)
        self.assertIn("accountable_note", result)

    def test_user_queryset(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertEqual(len(results), 3)
        result = results[0]
        self.assertNotIn("accountable", result)
        self.assertNotIn("accountable_note", result)

    def test_filter_by_model(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {"content_type__model": "user"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertEqual(len(results), 1)

    def test_filter_by_status(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url, {"status": "3"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertEqual(len(results), 1)

    def test_email_unverified(self):
        self.user.email_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
