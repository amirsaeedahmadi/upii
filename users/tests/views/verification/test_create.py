import shutil
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.models.verification import VerificationRequest
from users.tests.factories import CompanyFactory
from users.tests.factories import CompanyVerificationFactory
from users.tests.factories import UserFactory
from users.tests.factories import UserVerificationFactory
from utils.files import uploaded_image_file


class CreateVerificationRequestTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("verificationrequest-list")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(
            email="user@g.com",
            email_verified=True,
            shahkar_verified=True,
            mobile_verified=False,
            identity_verified=False,
        )
        cls.company = CompanyFactory(
            user=cls.user, ceo_shahkar_verified=True, ceo_mobile_verified=True
        )

    def tearDown(self):
        if Path(settings.MEDIA_ROOT).exists():
            shutil.rmtree(settings.MEDIA_ROOT)

    def test_model_is_required_before_anything(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_model(self):
        response = self.client.post(self.url, data={"model": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated(self):
        response = self.client.post(self.url, data={"model": "user"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_host(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url, data={"model": "user"}, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_email_unverified(self):
        self.user.email_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)

        # for user verification
        response = self.client.post(self.url, data={"model": "user"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # for company verification
        response = self.client.post(self.url, data={"model": "company"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_shahkar_unverified(self):
        self.user.shahkar_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)

        # for user verification
        response = self.client.post(self.url, data={"model": "user"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # for company verification
        response = self.client.post(self.url, data={"model": "company"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ceo_shahkar_unverified(self):
        self.company.ceo_shahkar_verified = False
        self.company.save()
        self.client.force_authenticate(self.user)
        data = {"model": "company"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ceo_mobile_unverified(self):
        self.company.ceo_mobile_verified = False
        self.company.save()
        self.client.force_authenticate(self.user)
        data = {"model": "company"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_documents_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data={"model": "user"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_document_tp_invalid(self):
        self.client.force_authenticate(self.user)
        data = {"model": "user", "10": uploaded_image_file()}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_existing_verified_request(self):
        ver = CompanyVerificationFactory(status=VerificationRequest.VERIFIED)
        self.client.force_authenticate(ver.user)
        data = {"model": "company", "1": uploaded_image_file()}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_existing_sent_verification(self):
        ver = CompanyVerificationFactory(status=VerificationRequest.SENT)
        self.client.force_authenticate(ver.user)
        data = {"model": "company", "1": uploaded_image_file()}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_existing_inspecting_verification(self):
        ver = UserVerificationFactory(status=VerificationRequest.INSPECTING)
        self.client.force_authenticate(ver.user)
        data = {"model": "user", "1": uploaded_image_file()}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_existing_rejected_verification(self, mocked_delay):
        ver = UserVerificationFactory(status=VerificationRequest.REJECTED)
        self.client.force_authenticate(ver.user)
        data = {"model": "user", "1": uploaded_image_file()}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mocked_delay.assert_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_successful(self, mocked_delay):
        self.client.force_authenticate(self.user)
        data = {
            "model": "company",
            "1": uploaded_image_file(),
            "2": uploaded_image_file(),
            "user_comment": "my comment",
        }
        response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertNotIn("accountable", data)
        self.assertNotIn("accountable_note", data)
        self.assertIn("user", data)
        self.assertIn("accountable_comment", data)
        self.assertIn("user_comment", data)
        self.assertIn("status_display", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], VerificationRequest.SENT)
        self.assertEqual(data["user_comment"], "my comment")
        self.assertIn("documents", data)
        self.assertEqual(len(data["documents"]), 2)
        self.assertNotIn("file", data["documents"][0])
        self.assertIn("download_url", data["documents"][0])
        self.assertIsNotNone(data["documents"][0]["download_url"])
        mocked_delay.assert_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_accountable_comment_and_note_is_ignored(self, mocked_delay):
        self.client.force_authenticate(self.user)
        data = {
            "model": "company",
            "1": uploaded_image_file(),
            "2": uploaded_image_file(),
            "user_comment": "my comment",
            "accountable_comment": "accountable comment",
            "accountable_note": "accountable note",
        }
        response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("accountable_comment", data)
        self.assertIn("user_comment", data)
        self.assertEqual(data["accountable_comment"], "")
        vr = VerificationRequest.objects.get(pk=data["id"])
        self.assertEqual(vr.accountable_note, "")
