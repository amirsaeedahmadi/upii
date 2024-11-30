from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class GetUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="user@g.com")
        cls.staff = UserFactory(is_staff=True)
        cls.superuser = UserFactory(is_superuser=True)
        cls.url = reverse("user-detail", kwargs={"pk": cls.user.pk})

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ordinary_user_permission(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ordinary_staff_permission(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_with_read_permission(self):
        self.staff.access_list = ["users.view"]
        self.staff.save()
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["id"], str(self.user.pk))
