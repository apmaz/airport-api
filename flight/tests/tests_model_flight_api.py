from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import F
from django.db.models.aggregates import Count
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from flight.models import (
    Airplane,
    AirplaneType,
    Airport,
    Crew,
    Flight,
    Route,
)
from flight.serializers import FlightListSerializer, FlightRetrieveSerializer


FLIGHT_URL = reverse("flight:flight-list")


def sample_airplane_type(**kwargs) -> AirplaneType:
    defaults = {
        "name": "Boeing 747",
    }
    defaults.update(**kwargs)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(airplane_type=None, **kwargs) -> Airplane:
    if airplane_type is None:
        airplane_type = AirplaneType.objects.create(name="Boeing 747")
    defaults = {
        "name": "BH 10",
        "rows": 20,
        "seats_in_row": 6,
        "airplane_type": airplane_type,
    }
    defaults.update(**kwargs)
    return Airplane.objects.create(**defaults)


def sample_airport(**kwargs) -> Airport:
    defaults = {
        "name": "LA Airport",
        "location_city": "Los Angeles",
        "closest_big_city": "Los Angeles",
    }
    defaults.update(**kwargs)
    return Airport.objects.create(**defaults)


def sample_route(source=None, destination=None, **kwargs) -> Route:
    if source is None:
        source = Airport.objects.create(
            name="LA Airport",
            location_city="Los Angeles",
            closest_big_city="Los Angeles",
        )
    if destination is None:
        destination = Airport.objects.create(
            name="London Airport",
            location_city="London",
            closest_big_city="London",
        )
    defaults = {
        "source": source,
        "destination": destination,
        "distance": 5000,
    }
    defaults.update(**kwargs)
    return Route.objects.create(**defaults)


def sample_crew(**kwargs) -> Crew:
    defaults = {
        "first_name": "Peter",
        "last_name": "Jefferson",
    }
    defaults.update(**kwargs)
    return Crew.objects.create(**defaults)


def flight_get_url(flight):
    return reverse("flight:flight-detail", args=[flight.id])


class BaseFlightAPITest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.crew_1 = sample_crew()
        self.crew_2 = sample_crew(
            first_name="Alex",
            last_name="Anderson",
        )
        self.airport_1 = sample_airport(
            name="New-York Airport",
            location_city="New York",
            closest_big_city="New York",
        )
        self.airport_2 = sample_airport(
            name="LA Airport",
            location_city="Los Angeles",
            closest_big_city="Los Angeles",
        )
        self.airport_3 = sample_airport(
            name="Chicago Airport",
            location_city="Chicago",
            closest_big_city="Chicago",
        )
        self.airport_4 = sample_airport(
            name="Buda-Pest Airport",
            location_city="Buda-Pest",
            closest_big_city="Buda-Pest",
        )

        self.airplane = sample_airplane()
        self.route_1 = sample_route(
            source=self.airport_1,
            destination=self.airport_2,
            distance=1000,
        )
        self.route_2 = sample_route(
            source=self.airport_3,
            destination=self.airport_4,
            distance=1000,
        )
        self.route_3 = sample_route(
            source=self.airport_1,
            destination=self.airport_4,
            distance=1000,
        )
        self.route_4 = sample_route(
            source=self.airport_2,
            destination=self.airport_3,
            distance=1000,
        )
        self.flight_1 = Flight.objects.create(
            route=self.route_1,
            airplane=self.airplane,
            departure_time=timezone.make_aware(datetime(2025, 9, 10, 17, 00)),
            arrival_time=timezone.make_aware(datetime(2025, 9, 10, 20, 00)),
        )
        self.flight_1.crew.add(self.crew_1, self.crew_2)

        self.flight_2 = Flight.objects.create(
            route=self.route_2,
            airplane=self.airplane,
            departure_time=timezone.make_aware(datetime(2025, 9, 16, 22, 00)),
            arrival_time=timezone.make_aware(datetime(2025, 9, 17, 6, 00)),
        )
        self.flight_2.crew.add(self.crew_1, self.crew_2)

        self.flight_3 = Flight.objects.create(
            route=self.route_3,
            airplane=self.airplane,
            departure_time=timezone.make_aware(datetime(2025, 9, 17, 14, 30)),
            arrival_time=timezone.make_aware(datetime(2025, 9, 18, 2, 00)),
        )
        self.flight_3.crew.add(self.crew_1, self.crew_2)


class UnauthenticatedFlightSearchByQueryParamsTest(BaseFlightAPITest):
    def setUp(self):
        super().setUp()

    def test_returns_401_for_unauthenticated_user_crew(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightSearchByQueryParamsTest(BaseFlightAPITest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)

        flights = Flight.objects.all().annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row")
                - Count("tickets", distinct=True)
            )
        )

        self.flight_1 = flights.get(id=self.flight_1.id)
        self.flight_2 = flights.get(id=self.flight_2.id)
        self.flight_3 = flights.get(id=self.flight_3.id)

    def test_search_filter_flight_by_source_id(self):
        res = self.client.get(FLIGHT_URL, {"flight_source": f"{self.airport_1.id}"})
        serializer_with_search_source_1 = FlightListSerializer(self.flight_1)
        serializer_with_search_source_2 = FlightListSerializer(self.flight_3)
        serializer_without_search_source_1 = FlightListSerializer(self.flight_2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_with_search_source_1.data, res.data["results"])
        self.assertIn(serializer_with_search_source_2.data, res.data["results"])
        self.assertNotIn(serializer_without_search_source_1.data, res.data["results"])

    def test_search_filter_flight_by_destination_id(self):
        res = self.client.get(FLIGHT_URL, {"flight_destination": f"{self.airport_2.id}"})
        serializer_with_search_destination_1 = FlightListSerializer(self.flight_1)
        serializer_without_search_destination_1 = FlightListSerializer(self.flight_2)
        serializer_without_search_destination_2 = FlightListSerializer(self.flight_3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_with_search_destination_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_destination_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_destination_2.data, res.data["results"])

    def test_search_filter_flight_by_source_id_and_destination_id(self):
        res = self.client.get(
            FLIGHT_URL,
            {
                "flight_source": f"{self.airport_1.id}",
                "flight_destination": f"{self.airport_2.id}",
            },
        )
        serializer_with_search_source_and_destination_1 = FlightListSerializer(self.flight_1)
        serializer_without_search_source_and_destination_1 = FlightListSerializer(self.flight_2)
        serializer_without_search_source_and_destination_2 = FlightListSerializer(self.flight_3)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_with_search_source_and_destination_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_source_and_destination_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_source_and_destination_2.data, res.data["results"])

    def test_search_filter_flight_by_departure_time(self):
        res = self.client.get(FLIGHT_URL, {"departure_time": "2025-09-17-14:30"})
        serializer_with_search_departure_time_1 = FlightListSerializer(self.flight_3)
        serializer_without_search_departure_time_1 = FlightListSerializer(self.flight_1)
        serializer_without_search_departure_time_2 = FlightListSerializer(self.flight_2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_with_search_departure_time_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_departure_time_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_departure_time_2.data, res.data["results"])

    def test_search_filter_flight_by_arrival_time(self):
        res = self.client.get(FLIGHT_URL, {"arrival_time": "2025-09-10-20:00"})
        serializer_with_search_arrival_time_1 = FlightListSerializer(self.flight_1)
        serializer_without_search_arrival_time_1 = FlightListSerializer(self.flight_3)
        serializer_without_search_arrival_time_2 = FlightListSerializer(self.flight_2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_with_search_arrival_time_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_arrival_time_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_arrival_time_2.data, res.data["results"])

    def test_search_filter_flight_by_departure_and_arrival_time(self):
        res = self.client.get(
            FLIGHT_URL,
            {
                "departure_time": "2025-09-16-22:00",
                "arrival_time": "2025-09-17-6:00",
            },
        )
        serializer_with_search_departure_and_arrival_time_1 = FlightListSerializer(self.flight_2)
        serializer_without_search_departure_and_arrival_time_1 = FlightListSerializer(self.flight_3)
        serializer_without_search_departure_and_arrival_time_2 = FlightListSerializer(self.flight_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_with_search_departure_and_arrival_time_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_departure_and_arrival_time_1.data, res.data["results"])
        self.assertNotIn(serializer_without_search_departure_and_arrival_time_2.data, res.data["results"])


class UnauthenticatedFlightApiTest(BaseFlightAPITest):
    def setUp(self):
        super().setUp()

    def test_unauthenticated_user_flight_list_returns_401(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_flight_retrieve_returns_401(self):
        url = flight_get_url(self.flight_1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_flight_returns_401(self):
        payload = {
            "route": self.route_1,
            "airplane": self.airplane,
            "departure_time": timezone.make_aware(datetime(2025, 9, 12, 14, 00)),
            "arrival_time": timezone.make_aware(datetime(2025, 9, 12, 19, 00)),
        }
        res = self.client.post(FLIGHT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_patch_flight_returns_401(self):
        url = flight_get_url(self.flight_1)
        payload = {
            "departure_time": timezone.make_aware(datetime(2025, 9, 14, 14, 00)),
            "arrival_time": timezone.make_aware(datetime(2025, 9, 14, 19, 00)),
        }
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_put_flight_returns_401(self):
        url = flight_get_url(self.flight_1)
        payload = {
            "route": self.route_2,
            "airplane": self.airplane,
            "departure_time": timezone.make_aware(datetime(2025, 9, 12, 14, 00)),
            "arrival_time": timezone.make_aware(datetime(2025, 9, 12, 19, 00)),
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_for_unauthenticated_user_cannot_delete_flight_returns_401(self):
        url = flight_get_url(self.flight_1)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTest(BaseFlightAPITest):
    def setUp(self):
        super().setUp()
        user = get_user_model().objects.create_user(
            email="user@user.com",
            password="password",
        )
        self.client.force_authenticate(user=user)

    def test_authenticated_user_flight_list_returns_200(self):
        res = self.client.get(FLIGHT_URL)
        flights = Flight.objects.all().annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row") -
                Count("tickets", distinct=True)
            )
        )
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_authenticated_user_flight_retrieve_returns_200(self):
        url = flight_get_url(self.flight_1)
        res = self.client.get(url)
        serializer = FlightRetrieveSerializer(self.flight_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_authenticated_user_cannot_create_flight_returns_403(self):
        payload = {
            "route": self.route_1,
            "airplane": self.airplane,
            "departure_time": timezone.make_aware(datetime(2025, 9, 12, 14, 00)),
            "arrival_time": timezone.make_aware(datetime(2025, 9, 12, 19, 00)),
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_patch_flight_returns_403(self):
        url = flight_get_url(self.flight_1)
        payload = {
            "departure_time": timezone.make_aware(datetime(2025, 9, 14, 14, 00)),
            "arrival_time": timezone.make_aware(datetime(2025, 9, 14, 19, 00)),
        }
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_put_flight_returns_403(self):
        url = flight_get_url(self.flight_1)
        payload = {
            "route": self.route_2,
            "airplane": self.airplane,
            "departure_time": timezone.make_aware(datetime(2025, 9, 12, 14, 00)),
            "arrival_time": timezone.make_aware(datetime(2025, 9, 12, 19, 00)),
        }
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_delete_flight_returns_403(self):
        url = flight_get_url(self.flight_1)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_pagination(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("next", res.data)
        self.assertIn("previous", res.data)
        self.assertIn("results", res.data)


class AuthenticatedFlightThrottlingApiTest(BaseFlightAPITest):
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
            res = self.client.get(FLIGHT_URL)
            self.assertNotEqual(
                res.status_code, status.HTTP_429_TOO_MANY_REQUESTS
            )
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AdminFlightApiTest(BaseFlightAPITest):
    def setUp(self):
        super().setUp()
        admin = get_user_model().objects.create_user(
            email="admin@admin.com",
            password="password",
            is_staff=True
        )
        self.client.force_authenticate(user=admin)

    def test_admin_flight_list_returns_200(self):
        res = self.client.get(FLIGHT_URL)
        flights = Flight.objects.all().annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row") -
                Count("tickets", distinct=True)
            )
        )
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_admin_flight_retrieve_returns_200(self):
        url = flight_get_url(self.flight_1)
        res = self.client.get(url)
        serializer = FlightRetrieveSerializer(self.flight_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_admin_create_flight_returns_201(self):
        departure_time = timezone.make_aware(datetime(2025, 9, 12, 14, 00))
        arrival_time = timezone.make_aware(datetime(2025, 9, 12, 19, 00))
        payload = {
            "route": self.route_1.id,
            "airplane": self.airplane.id,
            "crew": (self.crew_1.id, self.crew_2.id),
            "departure_time": departure_time,
            "arrival_time": arrival_time,
        }
        res = self.client.post(FLIGHT_URL, payload)
        flight = Flight.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["route"], flight.route.id)
        self.assertEqual(payload["airplane"], flight.airplane.id)
        self.assertEqual(payload["departure_time"], flight.departure_time)
        self.assertEqual(payload["arrival_time"], flight.arrival_time)
        self.assertEqual(sorted(payload["crew"]), sorted(flight.crew.values_list("id", flat=True)))
        self.assertEqual(len(payload["crew"]), flight.crew.count())

    def test_admin_create_duplicate_flight_returns_400(self):
        departure_time = timezone.make_aware(datetime(2025, 9, 10, 17, 00))
        arrival_time = timezone.make_aware(datetime(2025, 9, 10, 20, 00))
        payload = {
            "route": self.route_1.id,
            "airplane": self.airplane.id,
            "crew": (self.crew_1.id, self.crew_2.id),
            "departure_time": departure_time,
            "arrival_time": arrival_time,
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_flight_without_route_returns_400(self):
        departure_time = timezone.make_aware(datetime(2025, 9, 12, 14, 00))
        arrival_time = timezone.make_aware(datetime(2025, 9, 12, 19, 00))
        payload = {
            "route": "",
            "airplane": self.airplane.id,
            "crew": (self.crew_1.id, self.crew_2.id),
            "departure_time": departure_time,
            "arrival_time": arrival_time,
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_flight_without_airplane_returns_400(self):
        departure_time = timezone.make_aware(datetime(2025, 9, 12, 14, 00))
        arrival_time = timezone.make_aware(datetime(2025, 9, 12, 19, 00))
        payload = {
            "route": self.route_1.id,
            "airplane": "",
            "crew": (self.crew_1.id, self.crew_2.id),
            "departure_time": departure_time,
            "arrival_time": arrival_time,
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_flight_without_departure_time_returns_400(self):
        arrival_time = timezone.make_aware(datetime(2025, 9, 12, 19, 00))
        payload = {
            "route": self.route_1.id,
            "airplane": self.airplane.id,
            "crew": (self.crew_1.id, self.crew_2.id),
            "departure_time": "",
            "arrival_time": arrival_time,
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_flight_without_arrival_time_returns_400(self):
        departure_time = timezone.make_aware(datetime(2025, 9, 12, 14, 00))
        payload = {
            "route": self.route_1.id,
            "airplane": "",
            "crew": (self.crew_1.id, self.crew_2.id),
            "departure_time": departure_time,
            "arrival_time": "",
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_flight_without_crew_returns_400(self):
        departure_time = timezone.make_aware(datetime(2025, 9, 12, 14, 00))
        arrival_time = timezone.make_aware(datetime(2025, 9, 12, 19, 00))
        payload = {
            "route": self.route_1.id,
            "airplane": self.airplane.id,
            "crew": [],
            "departure_time": departure_time,
            "arrival_time": arrival_time,
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_patch_flight_returns_201(self):
        url = flight_get_url(self.flight_1)
        payload = {
            "route": self.route_2.id,
            "crew": (self.crew_1.id,),
        }
        res = self.client.patch(url, payload)
        flight = Flight.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["route"], flight.route.id)
        self.assertEqual(sorted(payload["crew"]), sorted(flight.crew.values_list("id", flat=True)))
        self.assertEqual(len(payload["crew"]), flight.crew.count())

    def test_admin_put_flight_returns_201(self):
        url = flight_get_url(self.flight_1)
        departure_time = timezone.make_aware(datetime(2025, 9, 11, 14, 00))
        arrival_time = timezone.make_aware(datetime(2025, 9, 11, 19, 00))
        payload = {
            "route": self.route_2.id,
            "airplane": self.airplane.id,
            "crew": (self.crew_1.id,),
            "departure_time": departure_time,
            "arrival_time": arrival_time,
        }
        res = self.client.put(url, payload)
        flight = Flight.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["route"], flight.route.id)
        self.assertEqual(payload["airplane"], flight.airplane.id)
        self.assertEqual(payload["departure_time"], flight.departure_time)
        self.assertEqual(payload["arrival_time"], flight.arrival_time)
        self.assertEqual(sorted(payload["crew"]), sorted(flight.crew.values_list("id", flat=True)))
        self.assertEqual(len(payload["crew"]), flight.crew.count())

    def test_admin_delete_crew_returns_204(self):
        url = flight_get_url(self.flight_1)
        res = self.client.delete(url)

        self.assertFalse(
            Flight.objects.filter(id=self.flight_1.id).exists(),
            msg=f"Flight {self.flight_1.id} was not deleted"
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
