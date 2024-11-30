from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class LogoutTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.logout_url = reverse("logout")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@g.com")

    def test_successful(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_already_logged_out(self):
        response = self.client.post(
            self.logout_url,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
