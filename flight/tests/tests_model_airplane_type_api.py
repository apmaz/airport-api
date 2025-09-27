from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APIClient

from flight.models import AirplaneType
from flight.serializers import AirplaneTypeSerializer


AIRPLANE_TYPE_URL = reverse("flight:airplane-type-list")


def airplane_type_get_url(airplane_type) -> str:
    return reverse("flight:airplane-type-detail", args=[airplane_type.id])


def sample_airplane_type(**kwargs) -> AirplaneType:
    defaults = {
        "name": "Boeing 747",
    }
    defaults.update(**kwargs)
    return AirplaneType.objects.create(**defaults)


class BaseAirplaneTypeAPITest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.airplane_type_1 = sample_airplane_type()
        self.airplane_type_2 = sample_airplane_type(name="Boeing 748")


class UnauthenticatedAirplaneTypeApiTest(BaseAirplaneTypeAPITest):
    def test_unauthenticated_user_airplane_type_list_returns_401(self):
        res = self.client.get(AIRPLANE_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_airplane_type_retrieve_returns_401(self):
        url = airplane_type_get_url(self.airplane_type_1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_airplane_type_returns_401(self):
        payload = {"name": "Boeing 748"}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_patch_airplane_type_returns_401(self):
        url = airplane_type_get_url(self.airplane_type_1)
        payload = {"name": "Boeing 748"}
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_put_airplane_type_returns_401(self):
        url = airplane_type_get_url(self.airplane_type_1)
        payload = {"name": "Boeing 748"}
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_delete_airplane_type_returns_401(self):
        url = airplane_type_get_url(self.airplane_type_1)
        res = self.client.delete(url)
        self.assertTrue(
            AirplaneType.objects.filter(id=self.airplane_type_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneTypeApiTest(BaseAirplaneTypeAPITest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_airplane_type_list_returns_200(self):
        res = self.client.get(AIRPLANE_TYPE_URL)
        airplane_types = AirplaneType.objects.all()
        serializer = AirplaneTypeSerializer(airplane_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_authenticated_user_airplane_type_retrieve_returns_200(self):
        url = airplane_type_get_url(self.airplane_type_1)
        res = self.client.get(url)
        serializer = AirplaneTypeSerializer(self.airplane_type_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_authenticated_user_cannot_create_airplane_type_returns_403(self):
        payload = {"name": "Boeing 748"}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_patch_airplane_type_returns_403(self):
        url = airplane_type_get_url(self.airplane_type_1)
        payload = {"name": "Boeing 748"}
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_put_airplane_type_returns_403(self):
        url = airplane_type_get_url(self.airplane_type_1)
        payload = {"name": "Boeing 748"}
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_delete_airplane_type_returns_403(self):
        url = airplane_type_get_url(self.airplane_type_1)
        res = self.client.delete(url)
        self.assertTrue(
            AirplaneType.objects.filter(id=self.airplane_type_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_pagination(self):
        res = self.client.get(AIRPLANE_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("next", res.data)
        self.assertIn("previous", res.data)
        self.assertIn("results", res.data)


class AuthenticatedAirplaneTypeThrottlingApiTest(BaseAirplaneTypeAPITest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)
        cache.clear()

    def test_authenticated_user_exceeds_throttling_limit_returns_429(self):
        for _ in range(100):
            res = self.client.get(AIRPLANE_TYPE_URL)
            self.assertNotEqual(
                res.status_code, status.HTTP_429_TOO_MANY_REQUESTS
            )

        res = self.client.get(AIRPLANE_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AdminAirplaneTypeApiTest(BaseAirplaneTypeAPITest):
    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_user(
            email="admin@test.com",
            password="password",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin)

    def test_admin_create_duplicate_airplane_type_returns_400(self):
        payload = {"name": self.airplane_type_1.name}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_airplane_type_list_returns_200(self):
        res = self.client.get(AIRPLANE_TYPE_URL)
        airplane_types = AirplaneType.objects.all()
        serializer = AirplaneTypeSerializer(airplane_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_admin_airplane_type_retrieve_returns_200(self):
        url = airplane_type_get_url(self.airplane_type_1)
        res = self.client.get(url)
        serializer = AirplaneTypeSerializer(self.airplane_type_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_admin_create_airplane_type_returns_201(self):
        payload = {"name": "Boeing 749"}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)
        airplane_type = AirplaneType.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["name"], airplane_type.name)

    def test_admin_cannot_create_airplane_type_without_name_returns_400(self):
        payload = {"name": ""}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_patch_airplane_type_returns_200(self):
        url = airplane_type_get_url(self.airplane_type_1)
        payload = {"name": "Boeing 749"}
        res = self.client.patch(url, payload)
        self.airplane_type_1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["name"], self.airplane_type_1.name)

    def test_admin_put_airplane_type_returns_200(self):
        url = airplane_type_get_url(self.airplane_type_1)
        payload = {"name": "Boeing 749"}
        res = self.client.put(url, payload)
        self.airplane_type_1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["name"], self.airplane_type_1.name)

    def test_admin_delete_airplane_type_returns_204(self):
        url = airplane_type_get_url(self.airplane_type_1)
        res = self.client.delete(url)

        self.assertFalse(
            AirplaneType.objects.filter(id=self.airplane_type_1.id).exists(),
            msg=f"Airplane {self.airplane_type_1.id} was not deleted"
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
