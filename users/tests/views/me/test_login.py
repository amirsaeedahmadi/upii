# ruff: noqa: S106
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class LoginTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("login")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@g.com", username="utest", password="1234")

    def test_already_logged_in(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            data={"email": "test@g.com", "password": "1234"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_by_email(self):
        with self.assertNumQueries(1):
            response = self.client.post(
                self.url,
                data={"email": "test@g.com", "password": "1234"},
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("user", data)

    def test_by_username(self):
        response = self.client.post(
            self.url,
            data={"email": "utest", "password": "1234"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("user", data)
