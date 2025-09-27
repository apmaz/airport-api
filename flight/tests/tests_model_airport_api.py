from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APIClient

from flight.models import Airport
from flight.serializers import AirportSerializer

AIRPORT_URL = reverse("flight:airport-list")


def airport_get_url(airport) -> str:
    return reverse(
        "flight:airport-detail",
        args=[airport.id]
    )


def sample_airport(**kwargs) -> Airport:
    defaults = {
        "name": "LA Airport",
        "location_city": "Los Angeles",
        "closest_big_city": "Los Angeles",
    }
    defaults.update(**kwargs)
    return Airport.objects.create(**defaults)


class BaseAirportAPITest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.airport_1 = sample_airport()
        self.airport_2 = sample_airport(
            name="London Airport",
            location_city="London",
            closest_big_city="London"
        )


class UnauthenticatedAirportApiTest(BaseAirportAPITest):
    def setUp(self):
        super().setUp()

    def test_unauthenticated_user_airport_list_returns_401(self):
        res = self.client.get(AIRPORT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_airport_retrieve_returns_401(self):
        url = airport_get_url(self.airport_1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_airport_returns_401(self):
        payload = {
            "name": "London Airport",
            "location_city": "London",
            "closest_big_city": "London"
        }
        res = self.client.post(AIRPORT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_patch_airport_returns_401(self):
        url = airport_get_url(self.airport_1)
        payload = {
            "name": "Los Angeles Airport"
        }
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_put_airport_returns_401(self):
        url = airport_get_url(self.airport_1)
        payload = {
            "name": "London Airport",
            "location_city": "London city",
            "closest_big_city": "London city"
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_delete_airport_returns_401(self):
        url = airport_get_url(self.airport_1)
        res = self.client.delete(url)
        self.assertTrue(
            Airport.objects.filter(id=self.airport_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportApiTest(BaseAirportAPITest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password"
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_airport_list_returns_200(self):
        res = self.client.get(AIRPORT_URL)
        airports = Airport.objects.all()
        serializer = AirportSerializer(airports, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_authenticated_user_airport_retrieve_returns_200(self):
        url = airport_get_url(self.airport_1)
        res = self.client.get(url)
        serializer = AirportSerializer(self.airport_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_authenticated_user_cannot_create_airport_returns_403(self):
        payload = {
            "name": "London Airport",
            "location_city": "London",
            "closest_big_city": "London"
        }
        res = self.client.post(AIRPORT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_patch_airport_returns_403(self):
        url = airport_get_url(self.airport_1)
        payload = {
            "name": "Los Angeles Airport"
        }
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_put_airport_returns_403(self):
        url = airport_get_url(self.airport_1)
        payload = {
            "name": "London Airport",
            "location_city": "London city",
            "closest_big_city": "London city"
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_delete_airport_returns_403(self):
        url = airport_get_url(self.airport_1)
        res = self.client.delete(url)
        self.assertTrue(
            Airport.objects.filter(id=self.airport_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_pagination(self):
        res = self.client.get(AIRPORT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("next", res.data)
        self.assertIn("previous", res.data)
        self.assertIn("results", res.data)


class AuthenticatedAirportThrottlingApiTest(BaseAirportAPITest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password"
        )
        self.client.force_authenticate(user=self.user)
        cache.clear()

    def test_authenticated_user_exceeds_throttling_limit_returns_429(self):
        for _ in range(100):
            res = self.client.get(AIRPORT_URL)
            self.assertNotEqual(
                res.status_code, status.HTTP_429_TOO_MANY_REQUESTS
            )
        res = self.client.get(AIRPORT_URL)
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AdminAirportApiTest(BaseAirportAPITest):
    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_user(
            email="admin@test.com",
            password="password",
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin)

    def test_admin_create_duplicate_airport_returns_400(self):
        payload = {
            "name": self.airport_1.name,
            "location_city": self.airport_1.location_city,
            "closest_big_city": self.airport_1.closest_big_city
        }
        res = self.client.post(AIRPORT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_airport_list_returns_200(self):
        res = self.client.get(AIRPORT_URL)
        airports = Airport.objects.all()
        serializer = AirportSerializer(airports, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_admin_airport_retrieve_returns_200(self):
        url = airport_get_url(self.airport_1)
        res = self.client.get(url)
        serializer = AirportSerializer(self.airport_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_admin_create_airport_returns_201(self):
        payload = {
            "name": "NY Airport",
            "location_city": "New York",
            "closest_big_city": "New York"
        }
        res = self.client.post(AIRPORT_URL, payload)
        airport = Airport.objects.get(id=res.data["id"])
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(airport, key))

    def test_admin_create_airport_without_name_returns_400(self):
        payload = {
            "name": "",
            "location_city": "New York",
            "closest_big_city": "New York"
        }
        res = self.client.post(AIRPORT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_airport_without_location_city_returns_400(self):
        payload = {
            "name": "NY Airport",
            "location_city": "",
            "closest_big_city": "New York"
        }
        res = self.client.post(AIRPORT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_airport_without_closest_big_city_returns_201(self):
        payload = {
            "name": "NY Airport",
            "location_city": "New York",
            "closest_big_city": ""
        }
        res = self.client.post(AIRPORT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_admin_patch_airport_returns_200(self):
        url = airport_get_url(self.airport_1)
        payload = {
            "name": "Los Angeles Airport"
        }
        res = self.client.patch(url, payload)
        self.airport_1.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["name"], self.airport_1.name)

    def test_admin_put_airport_returns_200(self):
        url = airport_get_url(self.airport_1)
        payload = {
            "name": "Los Angeles Airport",
            "location_city": "Los Angeles",
            "closest_big_city": "Los Angeles"
        }
        res = self.client.put(url, payload)
        self.airport_1.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key in payload:
            self.assertEqual(payload[key], getattr(self.airport_1, key))

    def test_admin_delete_airport_returns_204(self):
        url = airport_get_url(self.airport_1)
        res = self.client.delete(url)
        self.assertFalse(
            Airport.objects.filter(id=self.airport_1.id).exists(),
            msg=f"Airport {self.airport_1.id} was not deleted"
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
