from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.shahkar import ShahkarResponse
from users.tests.factories import UserFactory


class VerifyShahkarTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("verify-shahkar")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="user@g.com", email_verified=True)

    def test_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_email_unverified(self):
        self.user.email_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_already_verified(self):
        self.user.shahkar_verified = True
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_national_code_required(self):
        self.client.force_authenticate(self.user)
        data = {
            "mobile": "09122005747",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_required(self):
        self.client.force_authenticate(self.user)
        data = {
            "national_code": "0072284846",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_mobile(self):
        self.client.force_authenticate(self.user)
        data = {
            "national_code": "0072284846",
            "mobile": "4444",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("utils.kafka.KafkaEventStore.add_event")
    @patch(
        "users.shahkar.shahkar.verify",
        return_value=(False, ShahkarResponse({"detail": "Fail"}, 401)),
    )
    def test_failure(self, verify_mock, add_event):
        self.client.force_authenticate(self.user)
        data = {
            "national_code": "0072284846",
            "mobile": "09122005747",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        verify_mock.assert_called_once()
        add_event.assert_not_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    @patch(
        "users.shahkar.shahkar.verify",
        return_value=(True, ShahkarResponse({"detail": "OK"}, 200)),
    )
    def test_successful(self, verify_mock, add_event):
        self.client.force_authenticate(self.user)
        data = {
            "national_code": "0072284846",
            "mobile": "09122005747",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        verify_mock.assert_called_once()
        add_event.assert_called()
