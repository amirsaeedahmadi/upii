from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.tests.factories import CompanyVerificationFactory
from users.tests.factories import UserFactory


class ListAssignablesTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = UserFactory(is_staff=True, roles=["verifications.accountable"])
        UserFactory(email="use12@gmail.com", is_staff=True)
        UserFactory(
            email="use123@gmail.com",
            is_staff=True,
            is_active=False,
            roles=["verifications.accountable"],
        )
        UserFactory(
            email="use1234@gmail.com",
            is_staff=True,
            roles=["verifications.accountable"],
        )
        UserFactory(
            email="use12345@gmail.com",
            is_staff=True,
            roles=["verifications.accountable"],
        )
        cls.request = CompanyVerificationFactory(accountable=cls.staff)
        cls.url = reverse(
            "verificationrequest-assignables", kwargs={"pk": cls.request.pk}
        )

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_not_admin_host(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_accountable(self):
        self.staff.roles = []
        self.staff.save()
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_is_required(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(
            self.url, {"search": "use"}, headers={"host": "api.admin.testserver"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        results = data["results"]
        self.assertEqual(len(results), 2)
        result = results[0]
        self.assertIn("email", result)
        self.assertIn("first_name", result)
        self.assertIn("last_name", result)
