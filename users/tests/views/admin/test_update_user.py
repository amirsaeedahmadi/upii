# ruff: noqa: S106
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory

User = get_user_model()


class UpdateUserTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="user@g.com", password="1234")
        cls.staff = UserFactory(is_staff=True)
        cls.superuser = UserFactory(is_superuser=True)
        cls.url = reverse("user-detail", kwargs={"pk": cls.user.pk})

    def test_unauthenticated(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ordinary_user_permission(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ordinary_staff_permission(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_with_only_write_permission(self):
        self.staff.access_list = ["users.change"]
        self.staff.save()
        self.client.force_authenticate(self.staff)
        response = self.client.patch(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_staff_with_read_and_write_permission(self, add_event):
        self.staff.access_list = ["users.view", "users.change"]
        self.staff.save()
        self.client.force_authenticate(self.staff)
        data = {"email": "new@g.com", "password": "1234"}
        response = self.client.patch(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        add_event.assert_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_successful(self, add_event):
        self.client.force_authenticate(self.superuser)
        data = {
            "email": "new@g.com",
            "password": "1234",
            "email_verified": True,
            "shahkar_verified": True,
            "is_active": False,
        }
        url = reverse("user-detail", kwargs={"pk": self.user.pk})
        response = self.client.patch(
            url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        add_event.assert_called_once()
