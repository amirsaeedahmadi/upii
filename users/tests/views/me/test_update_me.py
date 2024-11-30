# ruff: noqa: S106
from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class UpdateMeTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("me")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@g.com", password="1234", email_verified=True)

    def test_unauthenticated(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_if_email_unverified(self):
        self.user.email_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_successful(self, add_event):
        self.client.force_authenticate(self.user)
        data = {
            "email": "cant_change",
            "password": "cant_change",
            "is_active": "ignored",
            "email_verified": "ignored",
            "email_verified_at": "ignored",
            "mobile": "ignored",
            "mobile_verified": "ignored",
            "mobile_verified_at": "ignored",
            "shahkar_verified": "ignored",
            "shahkar_verified_at": "ignored",
            "national_code": "ignored",
            "avatar": "ignored",
            "avatar_updated_at": "ignored",
            "groups": "ignored",
            "user_permissions": "ignored",
            "is_staff": "ignored",
            "is_superuser": "ignored",
            "identity_verified": "ignored",
            "identity_verified_at": "ignored",
            "username": "ignored",
            "first_name": "changed_first_name",
            "last_name": "changed_last_name",
            "postal_code": 1234567890,
            "postal_address": "my address",
        }
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        add_event.assert_called_once()
        data = response.json()
        self.assertNotIn("password", data)
        self.assertNotIn("groups", data)
        self.assertNotIn("user_permissions", data)
        self.assertIn("is_staff", data)
        self.assertIn("is_superuser", data)

        # Ensure these data are not changed.
        # Other sensitive data are surely rejected in validation.
        self.assertEqual(data["is_active"], True)
