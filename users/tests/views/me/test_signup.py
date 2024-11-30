from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.shahkar import ShahkarResponse
from users.tests.factories import UserFactory


class SignupTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("signup")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="already@g.com")

    def test_admin_host(self):
        response = self.client.post(
            self.url,
            data={
                "email": "new@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
            headers={"host": "api.admin.testserver"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logged_in(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            self.url,
            data={
                "email": "new@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_existing_email(self):
        response = self.client.post(
            self.url,
            data={
                "email": "already@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_required(self):
        response = self.client.post(
            self.url,
            data={
                "username": "noemail@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_required(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_first_name_required(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "password": "1234",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_first_name_blank_not_allowed(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "password": "1234",
                "first_name": "",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_last_name_required(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "password": "1234",
                "first_name": "v",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_last_name_blank_not_allowed(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_national_code_required(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_national_code_blank_not_allowed(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_required(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mobile_blank_not_allowed(self):
        response = self.client.post(
            self.url,
            data={
                "email": "nopassword@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("utils.kafka.KafkaEventStore.add_event")
    @patch(
        "users.shahkar.shahkar.verify",
        return_value=(False, ShahkarResponse({"detail": "Fail"}, 401)),
    )
    def test_shahkar_failure(self, shahkar, add_event):
        response = self.client.post(
            self.url,
            data={
                "email": "new@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        shahkar.assert_called_once()
        add_event.assert_not_called()

    @patch("utils.kafka.KafkaEventStore.add_event")
    @patch(
        "users.shahkar.shahkar.verify",
        return_value=(True, ShahkarResponse({"detail": "OK"}, 200)),
    )
    def test_successful(self, shahkar, add_event):
        response = self.client.post(
            self.url,
            data={
                "email": "new@g.com",
                "password": "1234",
                "first_name": "v",
                "last_name": "d",
                "national_code": "0072284846",
                "mobile": "09122005747",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data.get("shahkar_verified"), True)
        self.assertEqual(data["national_code"], "0072284846")
        self.assertEqual(data["mobile"], "09122005747")
        shahkar.assert_called_once()
        add_event.assert_called_once()
