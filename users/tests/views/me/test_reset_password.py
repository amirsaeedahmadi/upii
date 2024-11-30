from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory
from utils.tokens import set_email_token_for_user


class ResetPasswordTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("reset-password")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="user@g.com")
        cls.code, expiry = set_email_token_for_user(cls.user)

    def test_authenticated(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_email_required(self):
        response = self.client.post(
            self.url,
            data={"code": self.code, "new_password": "@123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_code_required(self):
        response = self.client.post(
            self.url,
            data={"email": self.user.email, "new_password": "@123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_required(self):
        response = self.client.post(
            self.url,
            data={"email": self.user.email, "code": self.code},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_existing_email(self):
        data = {"email": "wrong@wrong.com", "code": self.code, "new_password": "@123"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_code(self):
        data = {"email": self.user.email, "code": 0000, "new_password": "@123"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        data = {"email": self.user.email, "code": self.code, "new_password": "@123"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("@123"))
