# ruff: noqa: S106
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class ChangeUsernameTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("change-username")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@g.com")

    def test_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={"username": "user1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "user1")

    def test_exisiting_username(self):
        self.user.username = "existing"
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            data={"username": "existing"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
