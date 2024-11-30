# ruff: noqa: S106
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class ChangePasswordTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("change-password")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@g.com", password="1234")

    def test_unauthenticated(self):
        response = self.client.post(
            self.url,
            data={"current_password": "1234", "new_password": "5678"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            data={"current_password": "1234", "new_password": "5678"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_current_password_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            data={"new_password": "5678"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_password_wrong(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            data={"current_password": "wrong", "new_password": "5678"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
