# ruff: noqa: S106
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class AdminLoginTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("login")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(
            email="test@g.com", username="utest", password="1234", is_staff=False
        )

    def test_not_staff(self):
        response = self.client.post(
            self.url,
            data={"email": "test@g.com", "password": "1234"},
            headers={"host": "api.admin.testserver"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
