from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class CheckAvailabilityTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("check-availability")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@g.com")

    def test_logged_in(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            data={"email": "new@g.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_email_required(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_email(self):
        response = self.client.post(self.url, data={"email": "testg.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        response = self.client.post(self.url, data={"email": "test@g.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("exists", data)
        self.assertEqual(data["exists"], True)
