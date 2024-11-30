from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.models.verification import VerificationRequest
from users.tests.factories import CompanyVerificationFactory
from users.tests.factories import UserFactory
from users.tests.factories import UserVerificationFactory


class InspectVerificationRequestTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = UserFactory(is_staff=True, roles=["verifications.accountable"])
        cls.company_request = CompanyVerificationFactory(accountable=cls.staff)
        cls.user_request = UserVerificationFactory(accountable=cls.staff)
        cls.user_request_url = reverse(
            "verificationrequest-inspect", kwargs={"pk": cls.user_request.pk}
        )
        cls.company_request_url = reverse(
            "verificationrequest-inspect", kwargs={"pk": cls.company_request.pk}
        )

    def test_unauthenticated(self):
        response = self.client.patch(self.user_request_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_not_admin_host(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(self.user_request_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_accountable(self):
        self.staff.roles = []
        self.staff.save()
        self.client.force_authenticate(self.staff)
        response = self.client.patch(
            self.user_request_url, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_is_required(self):
        self.client.force_authenticate(self.staff)
        data = {"accountable_comment": "accountable comment"}
        response = self.client.patch(
            self.user_request_url, data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_is_required_when_rejected(self):
        self.client.force_authenticate(self.staff)
        data = {"status": VerificationRequest.REJECTED}
        response = self.client.patch(
            self.user_request_url, data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_blank_comment_is_ok_when_verified(self, mocked_add):
        self.client.force_authenticate(self.staff)
        data = {"status": VerificationRequest.VERIFIED, "accountable_comment": ""}
        response = self.client.patch(
            self.user_request_url, data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_add.assert_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_comment_is_not_required_when_verified(self, mocked_add):
        self.client.force_authenticate(self.staff)
        data = {"status": VerificationRequest.VERIFIED}
        response = self.client.patch(
            self.user_request_url, data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_add.assert_called()

    def test_already_inspected(self):
        self.client.force_authenticate(self.staff)
        self.user_request.status = VerificationRequest.REJECTED
        self.user_request.save()
        data = {"status": VerificationRequest.VERIFIED}
        response = self.client.patch(
            self.user_request_url, data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_rejected(self, mocked_add):
        self.client.force_authenticate(self.staff)
        data = {
            "status": VerificationRequest.REJECTED,
            "accountable_comment": "accountable comment",
        }
        response = self.client.patch(
            self.user_request_url, data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("accountable", data)
        self.assertIn("accountable_note", data)
        self.assertIn("user", data)
        self.assertIn("accountable_comment", data)
        self.assertIn("user_comment", data)
        self.assertIn("status_display", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], VerificationRequest.REJECTED)
        self.assertIn("documents", data)
        self.user_request.user.refresh_from_db()
        self.assertEqual(self.user_request.user.identity_verified, False)
        mocked_add.assert_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_verified(self, mocked_add):
        self.client.force_authenticate(self.staff)
        data = {
            "status": VerificationRequest.VERIFIED,
        }
        response = self.client.patch(
            self.user_request_url, data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], VerificationRequest.VERIFIED)
        self.user_request.user.refresh_from_db()
        self.assertEqual(self.user_request.user.identity_verified, True)
        mocked_add.assert_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_company(self, mocked_add):
        self.client.force_authenticate(self.staff)
        data = {
            "status": VerificationRequest.VERIFIED,
        }
        response = self.client.patch(
            self.company_request_url, data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], VerificationRequest.VERIFIED)
        self.company_request.user.company.refresh_from_db()
        self.assertEqual(self.company_request.user.company.verified, True)
        mocked_add.assert_called()
