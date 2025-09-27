from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APIClient

from flight.models import Airport, Route
from flight.serializers import RouteListSerializer, RouteRetrieveSerializer


ROUTE_URL = reverse("flight:route-list")


def route_get_url(route) -> str:
    return reverse("flight:route-detail", args=[route.id])


def sample_route(source=None, destination=None, **kwargs) -> Route:
    if source is None:
        source = Airport.objects.create(
            name="LA Airport",
            location_city="Los Angeles",
            closest_big_city="Los Angeles"
        )
    if destination is None:
        destination = Airport.objects.create(
            name="London Airport",
            location_city="London",
            closest_big_city="London"
        )
    defaults = {
        "source": source,
        "destination": destination,
        "distance": 5000,
    }
    defaults.update(**kwargs)

    return Route.objects.create(**defaults)


def sample_airport(**kwargs) -> Airport:
    defaults = {
        "name": "Toronto Airport",
        "location_city": "Toronto",
        "closest_big_city": "Toronto",
    }
    defaults.update(**kwargs)

    return Airport.objects.create(**defaults)


class BaseRouteTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.route_1 = sample_route()
        self.route_2 = sample_route(
            source=sample_airport(),
            destination=sample_airport(
                name="NYC Airport",
                location_city="New York",
                closest_big_city="New York"
            )
        )
        self.airport_1 = sample_airport(
            name="Warsaw Airport",
            location_city="Warsaw",
            closest_big_city="Warsaw"
        )
        self.airport_2 = sample_airport(
            name="Kiev Airport",
            location_city="Kiev",
            closest_big_city="Kiev"
        )


class UnauthenticatedRouteApiTest(BaseRouteTest):
    def setUp(self):
        super().setUp()

    def test_unauthenticated_user_route_list_returns_401(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_route_retrieve_returns_401(self):
        url = route_get_url(self.route_1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_route_returns_401(self):
        payload = {
            "source": self.airport_1.id,
            "destination": self.airport_2.id,
            "distance": 5000,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_patch_route_returns_401(self):
        url = route_get_url(self.route_1)
        payload = {"distance": 4000}
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_put_route_returns_401(self):
        url = route_get_url(self.route_1)
        payload = {
            "source": self.airport_1.id,
            "destination": self.airport_2.id,
            "distance": 1000,
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_delete_route_returns_401(self):
        url = route_get_url(self.route_1)
        res = self.client.delete(url)

        self.assertTrue(Route.objects.filter(id=self.route_1.id).exists())
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTest(BaseRouteTest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_route_list_returns_200(self):
        res = self.client.get(ROUTE_URL)
        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_authenticated_user_route_retrieve_returns_200(self):
        url = route_get_url(self.route_1)
        res = self.client.get(url)
        serializer = RouteRetrieveSerializer(self.route_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_authenticated_user_cannot_create_route_returns_403(self):
        payload = {
            "source": self.airport_1.id,
            "destination": self.airport_2.id,
            "distance": 5000,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_patch_route_returns_403(self):
        url = route_get_url(self.route_1)
        payload = {"distance": 4000}
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_put_route_returns_403(self):
        url = route_get_url(self.route_1)
        payload = {
            "source": self.airport_1.id,
            "destination": self.airport_2.id,
            "distance": 1000,
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_delete_route_returns_403(self):
        url = route_get_url(self.route_1)
        res = self.client.delete(url)

        self.assertTrue(Route.objects.filter(id=self.route_1.id).exists())
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_pagination(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("next", res.data)
        self.assertIn("previous", res.data)
        self.assertIn("results", res.data)


class AuthenticatedRouteThrottlingApiTest(BaseRouteTest):
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
            res = self.client.get(ROUTE_URL)
            self.assertNotEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AdminRouteApiTest(BaseRouteTest):
    def setUp(self):
        super().setUp()

        self.admin = get_user_model().objects.create_user(
            email="admin@test.com",
            password="password",
            is_staff=True,
        )

        self.client.force_authenticate(user=self.admin)

    def test_admin_cannot_create_duplicate_route_returns_400(self):
        payload = {
            "source": self.route_1.source.id,
            "destination": self.route_1.destination.id,
            "distance": 1000,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_create_route_with_equal_source_and_destination_returns_400(self):
        payload = {
            "source": self.airport_1.id,
            "destination": self.airport_1.id,
            "distance": 1000,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_route_list_returns_200(self):
        res = self.client.get(ROUTE_URL)
        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_admin_route_retrieve_returns_200(self):
        url = route_get_url(self.route_1)
        res = self.client.get(url)
        serializer = RouteRetrieveSerializer(self.route_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_admin_create_route_returns_201(self):
        payload = {
            "source": self.airport_1.id,
            "destination": self.airport_2.id,
            "distance": 1000,
        }
        res = self.client.post(ROUTE_URL, payload)
        route = Route.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["source"], route.source.id)
        self.assertEqual(payload["destination"], route.destination.id)
        self.assertEqual(payload["distance"], route.distance)

    def test_admin_create_route_without_source_returns_400(self):
        payload = {
            "source": "",
            "destination": self.airport_2.id,
            "distance": 1000,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_route_without_destination_returns_400_for(self):
        payload = {
            "source": self.airport_1.id,
            "destination": "",
            "distance": 1000,
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_route_without_distance_returns_400(self):
        payload = {
            "source": self.airport_1.id,
            "destination": self.airport_2.id,
            "distance": "",
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_patch_route_returns_200(self):
        url = route_get_url(self.route_1)
        payload = {"distance": 4000}
        res = self.client.patch(url, payload)
        self.route_1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["distance"], self.route_1.distance)

    def test_admin_put_route_returns_200(self):
        url = route_get_url(self.route_1)
        payload = {
            "source": self.airport_1.id,
            "destination": self.airport_2.id,
            "distance": 1000,
        }
        res = self.client.put(url, payload)
        self.route_1.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["source"], self.route_1.source.id)
        self.assertEqual(payload["destination"], self.route_1.destination.id)
        self.assertEqual(payload["distance"], self.route_1.distance)

    def test_admin_delete_route_returns_204(self):
        url = route_get_url(self.route_1)
        res = self.client.delete(url)

        self.assertFalse(Route.objects.filter(id=self.route_1.id).exists())
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
