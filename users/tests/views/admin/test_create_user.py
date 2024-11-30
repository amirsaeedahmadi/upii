# ruff: noqa: S106
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory

User = get_user_model()


class CreateUserTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("user-list")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.staff = UserFactory(is_staff=True)
        cls.superuser = UserFactory(is_superuser=True)

    def test_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ordinary_user_permission(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ordinary_staff_permission(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_with_only_write_permission(self):
        self.staff.access_list = ["users.change"]
        self.staff.save()
        self.client.force_authenticate(self.staff)
        data = {"email": "new@g.com", "password": "1234"}
        response = self.client.post(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_staff_with_read_and_write_permission(self, add_event):
        self.staff.access_list = ["users.view", "users.change"]
        self.staff.save()
        self.client.force_authenticate(self.staff)
        data = {"email": "new@g.com", "password": "1234"}
        response = self.client.post(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        add_event.assert_called()

    def test_valid_access_list_choices(self):
        self.client.force_authenticate(self.superuser)
        data = {"email": "new@g.com", "password": "1234", "access_list": ["invalid"]}
        response = self.client.post(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_role_list_choices(self):
        self.client.force_authenticate(self.superuser)
        data = {"email": "new@g.com", "password": "1234", "roles": ["invalid"]}
        response = self.client.post(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_access_list_and_roles_not_required(self, add_event):
        self.client.force_authenticate(self.superuser)
        data = {"email": "new@g.com", "password": "1234"}
        response = self.client.post(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        add_event.assert_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_create_non_staff_with_access_list_and_roles(self, add_event):
        self.client.force_authenticate(self.superuser)
        data = {
            "email": "new@g.com",
            "password": "1234",
            "access_list": ["users.view", "users.change"],
            "roles": ["verifications.accountable", "tickets.accountable"],
        }
        response = self.client.post(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        add_event.assert_called_once()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_create_non_staff_superuser_with_access_list_and_roles(self, add_event):
        self.client.force_authenticate(self.superuser)
        data = {
            "email": "new@g.com",
            "password": "1234",
            "is_superuser": True,
            "access_list": ["users.view", "users.change"],
            "roles": ["verifications.accountable", "tickets.accountable"],
        }
        response = self.client.post(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        add_event.assert_called_once()

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_successful(self, add_event):
        self.client.force_authenticate(self.superuser)
        data = {
            "email": "new@g.com",
            "password": "1234",
            "is_staff": True,
            "access_list": ["users.view", "users.change"],
            "roles": ["verifications.accountable", "tickets.accountable"],
        }
        response = self.client.post(
            self.url, data=data, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        add_event.assert_called_once()
