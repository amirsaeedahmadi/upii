from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class GetMeTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("me")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@g.com")

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertNotIn("password", data)
        self.assertNotIn("groups", data)
        self.assertNotIn("user_permissions", data)
        self.assertIn("is_staff", data)
        self.assertIn("is_superuser", data)
        self.assertIn("username", data)
        self.assertIn("email", data)
        self.assertIn("email_verified", data)
        self.assertIn("shahkar_verified", data)
        self.assertIn("mobile_verified", data)
        self.assertIn("identity_verified", data)
        self.assertIn("can_order", data)
        self.assertIn("is_active", data)
