from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory
from utils import tokens


class VerifyMobileTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("verify-mobile")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(
            email="user@g.com",
            email_verified=True,
            shahkar_verified=True,
        )
        cls.code, expiry = tokens.set_mobile_token_for_user(cls.user)

    def test_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_email_unverified(self):
        self.user.email_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_shahkar_unverified(self):
        self.user.shahkar_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_already_verified(self):
        self.user.mobile_verified = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_code(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={"code": self.code + "1"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_successful(self, add_event):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={"code": self.code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        add_event.assert_called()
