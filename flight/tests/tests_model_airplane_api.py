from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APIClient

from flight.models import AirplaneType, Airplane
from flight.serializers import (
    AirplaneListSerializer,
    AirplaneRetrieveSerializer,
)


AIRPLANE_URL = reverse("flight:airplane-list")


def airplane_get_url(airplane) -> str:
    return reverse("flight:airplane-detail", args=[airplane.id])


def sample_airplane(airplane_type=None, **kwargs) -> Airplane:
    if airplane_type is None:
        airplane_type = AirplaneType.objects.create(name="Boeing 747")
    defaults = {
        "name": "BH 17",
        "rows": 20,
        "seats_in_row": 6,
        "airplane_type": airplane_type,
    }
    defaults.update(**kwargs)

    return Airplane.objects.create(**defaults)


def sample_airplane_type(name=None, **kwargs) -> AirplaneType:
    if name is None:
        name = "Boeing 747"
    defaults = {
        "name": name,
    }
    defaults.update(**kwargs)

    return AirplaneType.objects.create(**defaults)


class BaseAirplaneAPITest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.airplane_1 = sample_airplane()
        self.airplane_2 = sample_airplane(
            airplane_type=sample_airplane_type(name="Boeing 748"),
            name="BH 18",
        )
        self.airplane_type_1 = sample_airplane_type(name="Boeing 749")


class UnauthenticatedAirplaneApiTest(BaseAirplaneAPITest):
    def setUp(self):
        super().setUp()

    def test_unauthenticated_user_airplane_list_returns_401(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_airplane_retrieve_returns_401(self):
        url = airplane_get_url(self.airplane_1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_airplane_returns_401(self):
        payload = {
            "name": "SH 18",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_patch_airplane_returns_401(self):
        url = airplane_get_url(self.airplane_1)
        payload = {
            "name": "SH 18",
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_put_airplane_returns_401(self):
        url = airplane_get_url(self.airplane_1)
        payload = {
            "name": "SH 18",
            "rows": 11,
            "seats_in_row": 5,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_delete_airplane_returns_401(self):
        url = airplane_get_url(self.airplane_1)
        res = self.client.delete(url)
        self.assertTrue(
            Airplane.objects.filter(id=self.airplane_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneApiTest(BaseAirplaneAPITest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_airplane_list_returns_200(self):
        res = self.client.get(AIRPLANE_URL)
        airplanes = Airplane.objects.all()
        serializer = AirplaneListSerializer(airplanes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_authenticated_user_airplane_retrieve_returns_200(self):
        url = airplane_get_url(self.airplane_1)
        res = self.client.get(url)
        serializer = AirplaneRetrieveSerializer(self.airplane_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_authenticated_user_cannot_create_airplane_returns_403(self):
        payload = {
            "name": "SH 18",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_patch_airplane_returns_403(self):
        url = airplane_get_url(self.airplane_1)
        payload = {
            "name": "SH 18",
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_put_airplane_returns_403(self):
        url = airplane_get_url(self.airplane_1)
        payload = {
            "name": "SH 18",
            "rows": 11,
            "seats_in_row": 5,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_delete_airplane_returns_403(self):
        url = airplane_get_url(self.airplane_1)
        res = self.client.delete(url)
        self.assertTrue(
            Airplane.objects.filter(id=self.airplane_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_pagination(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("next", res.data)
        self.assertIn("previous", res.data)
        self.assertIn("results", res.data)


class AuthenticatedAirplaneThrottlingApiTest(BaseAirplaneAPITest):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)
        cache.clear()

    def test_authenticated_user_exceeds_throttling_limit_returns_429(self):
        for _ in range(100):
            res = self.client.get(AIRPLANE_URL)
            self.assertNotEqual(
                res.status_code, status.HTTP_429_TOO_MANY_REQUESTS
            )

        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AdminAirplaneApiTest(BaseAirplaneAPITest):
    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_user(
            email="admin@test.com",
            password="password",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin)

    def test_admin_create_duplicate_airplane_returns_400(self):
        payload = {
            "name": self.airplane_1.name,
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_airplane_list_returns_200(self):
        res = self.client.get(AIRPLANE_URL)
        airplanes = Airplane.objects.all()
        serializer = AirplaneListSerializer(airplanes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_admin_airplane_retrieve_returns_200(self):
        url = airplane_get_url(self.airplane_1)
        res = self.client.get(url)
        serializer = AirplaneRetrieveSerializer(self.airplane_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_admin_create_airplane_returns_201(self):
        payload = {
            "name": "SH 17",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        airplane = Airplane.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            if key == "airplane_type":
                self.assertEqual(payload[key], airplane.airplane_type.id)
            else:
                self.assertEqual(payload[key], getattr(airplane, key))

    def test_admin_create_airplane_without_airplane_type_returns_400(self):
        payload = {
            "name": "SH 17",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": "",
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_airplane_without_name_returns_400(self):
        payload = {
            "name": "",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_airplane_without_rows_returns_400(self):
        payload = {
            "name": "SH 17",
            "rows": 0,
            "seats_in_row": 4,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_airplane_without_seats_in_row_returns_400(self):
        payload = {
            "name": "SH 17",
            "rows": 10,
            "seats_in_row": 0,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_patch_airplane_returns_200(self):
        url = airplane_get_url(self.airplane_1)
        payload = {
            "name": "SH 18",
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.patch(url, payload)
        self.airplane_1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key in payload:
            if key == "airplane_type":
                self.assertEqual(payload[key], self.airplane_1.airplane_type.id)
            else:
                self.assertEqual(payload[key], getattr(self.airplane_1, key))

    def test_admin_put_airplane_returns_200(self):
        url = airplane_get_url(self.airplane_1)
        payload = {
            "name": "SH 18",
            "rows": 11,
            "seats_in_row": 5,
            "airplane_type": self.airplane_type_1.id,
        }
        res = self.client.put(url, payload)
        self.airplane_1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key in payload:
            if key == "airplane_type":
                self.assertEqual(payload[key], self.airplane_1.airplane_type.id)
            else:
                self.assertEqual(payload[key], getattr(self.airplane_1, key))

    def test_admin_delete_airplane_returns_204(self):
        url = airplane_get_url(self.airplane_1)
        res = self.client.delete(url)

        self.assertFalse(
            Airplane.objects.filter(id=self.airplane_1.id).exists(),
            msg=f"Airplane {self.airplane_1.id} was not deleted"
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
