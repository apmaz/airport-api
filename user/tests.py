from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.cache import cache

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

USER_REGISTER_URL = reverse("user:register")
USER_ME_URL = reverse("user:manage_user")
USER_LOGIN_URL = reverse("user:token_obtain_pair")


class UnauthenticatedUser(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_unauthenticated_user_can_register_returns_201(self):
        payload = {
            "email": "user@user.com",
            "password": "password"
        }
        res = self.client.post(USER_REGISTER_URL, payload)
        created_user = get_user_model().objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["email"], created_user.email)
        self.assertTrue(
            get_user_model().objects.filter(id=created_user.id).exists()
        )

    def test_check_validation_email_field_returns_400(self):
        payload = {
            "email": "useruser.com",
            "password": "password"
        }
        res = self.client.post(USER_REGISTER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_validation_password_field_returns_400(self):
        payload = {
            "email": "user@user.com",
            "password": "p"
        }
        res = self.client.post(USER_REGISTER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_can_login_returns_200(self):
        get_user_model().objects.create_user(
            email="user@user.com",
            password="password",
        )
        payload = {
            "email": "user@user.com",
            "password": "password",
        }
        res = self.client.post(USER_LOGIN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_unauthenticated_user_cannot_get_access_to_manage_page_returns_401(self):
        payload = {
            "email": "user@user.com",
            "password": "password",
        }
        res = self.client.put(USER_ME_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUser(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            email="user@user.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)

    def test_registration_with_duplicate_email_returns_400(self):
        payload = {
            "email": "user@user.com",
            "password": "password",
        }
        res = self.client.post(USER_REGISTER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_can_update_personal_data_returns_200(self):
        payload = {
            "email": "user_1@user.com",
            "password": "passworD",
        }
        res = self.client.put(USER_ME_URL, payload)
        user = get_user_model().objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(user.email, payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

    def test_authenticated_user_cannot_change_value_is_staff_returns_200(self):
        payload = {
            "email": "user@user.com",
            "is_staff": True,
            "password": "password"
        }
        res = self.client.put(USER_ME_URL, payload)
        user = get_user_model().objects.get(id=self.user.id)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data["is_staff"])
        self.assertFalse(user.is_staff)
