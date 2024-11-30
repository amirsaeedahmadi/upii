# ruff: noqa: S106
from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class RequestResetPasswordTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("request-reset-password")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="user@g.com")

    def test_authenticated(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_email_required(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_email_not_existing(self, add_event):
        response = self.client.post(self.url, data={"email": "test@g.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        add_event.assert_not_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_successful(self, add_event):
        response = self.client.post(self.url, data={"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        add_event.assert_called_once()
