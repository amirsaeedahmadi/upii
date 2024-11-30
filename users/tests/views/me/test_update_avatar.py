from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory
from utils.files import uploaded_image_file


class UpdateAvatarTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("avatar")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@g.com", email_verified=True)

    def test_unauthenticated(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_if_email_unverified(self):
        self.user.email_verified = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_avatar_required(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        self.client.force_authenticate(self.user)
        data = {
            "avatar": uploaded_image_file(),
        }
        response = self.client.patch(self.url, data=data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
