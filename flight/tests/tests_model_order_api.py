from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APIClient

from flight.models import (
    Route,
    Airport,
    AirplaneType,
    Airplane,
    Flight,
    Crew,
    Order,
    Ticket
)
from flight.serializers import OrderListSerializer, OrderRetrieveSerializer

ORDER_URL = reverse("flight:order-list")


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


def sample_crew(**kwargs) -> Crew:
    defaults = {
        "first_name": "Peter",
        "last_name": "Jefferson",
    }
    defaults.update(**kwargs)

    return Crew.objects.create(**defaults)


def order_get_url(order):
    return reverse(
        "flight:order-detail",
        args=[order.id])


class BaseOrderAPITest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            email="admin@user.com",
            password="password",
            is_staff=True,
        )
        self.user_1 = get_user_model().objects.create_user(
            email="user_1@user.com",
            password="password",
        )
        self.user_2 = get_user_model().objects.create_user(
            email="user_2@user.com",
            password="password",
        )
        self.airport_1 = sample_airport(
            name="New-York Airport",
            location_city="New York",
            closest_big_city="New York"
        )
        self.airport_2 = sample_airport(
            name="LA Airport",
            location_city="Los Angeles",
            closest_big_city="Los Angeles"
        )
        self.crew = sample_crew(
            first_name="Piter",
            last_name="Peterson",
        )
        self.airplane_type = sample_airplane_type(name="Boeing 750")
        self.airplane = sample_airplane()
        self.route = sample_route(
            source=self.airport_1,
            destination=self.airport_2,
            distance=1000,
        )
        self.flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time=datetime(2025, 9, 10, 17, 00),
            arrival_time=datetime(2025, 9, 10, 19, 00),
        )
        self.flight.crew.set([self.crew.id])

        self.order_1 = Order.objects.create(
            user=self.user_1,
        )
        self.ticket_1_order_1 = Ticket.objects.create(
            row=1,
            seat=1,
            flight=self.flight,
            order=self.order_1,
        )

        self.order_2 = Order.objects.create(
            user=self.user_1,
        )
        self.ticket_1_order_2 = Ticket.objects.create(
            row=2,
            seat=1,
            flight=self.flight,
            order=self.order_2,
        )
        self.ticket_2_order_2 = Ticket.objects.create(
            row=2,
            seat=2,
            flight=self.flight,
            order=self.order_2,
        )

        self.order_3 = Order.objects.create(
            user=self.user_2,
        )
        self.ticket_1_order_3 = Ticket.objects.create(
            row=3,
            seat=1,
            flight=self.flight,
            order=self.order_3,
        )
        self.ticket_2_order_3 = Ticket.objects.create(
            row=3,
            seat=2,
            flight=self.flight,
            order=self.order_3,
        )


class UnauthenticatedOrderApiTest(BaseOrderAPITest):
    def setUp(self):
        super().setUp()

    def test_unauthenticated_user_order_list_returns_401(self):
        res = self.client.get(ORDER_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_order_retrieve_returns_401(self):
        url = order_get_url(self.order_1)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_order_returns_401(self):
        payload = {}
        res = self.client.post(ORDER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_patch_order_returns_401(self):
        url = order_get_url(self.order_1)
        payload = {}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_put_order_returns_401(self):
        url = order_get_url(self.order_1)
        payload = {}
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_delete_order_returns_401(self):
        url = order_get_url(self.order_1)
        res = self.client.delete(url)

        self.assertTrue(Order.objects.filter(
            id=self.order_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTest(BaseOrderAPITest):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user_1)


    def test_authenticated_user_can_see_only_their_own_order_list_returns_200(self):
        res = self.client.get(ORDER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for result in res.data["results"]:
            order = Order.objects.get(id=result["id"])
            self.assertEqual(order.user, self.user_1)

    def test_authenticated_user_does_not_have_access_to_other_users_orders_returns_404(self):
        url = order_get_url(self.order_3)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_user_order_retrieve_returns_200(self):
        url = order_get_url(self.order_1)
        res = self.client.get(url)
        serializer = OrderRetrieveSerializer(self.order_1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_authenticated_user_cannot_create_empty_order_returns_400(self):
        payload = {"user": self.user_1}
        res = self.client.post(ORDER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_create_order_with_tickets_returns_201(self):
        payload = {
            "tickets": [
                {
                    "flight": self.flight.id,
                    "row": 1,
                    "seat": 2
                },
                {
                    "flight": self.flight.id,
                    "row": 1,
                    "seat": 3
                }
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")
        order = Order.objects.get(id=res.data["id"])

        tickets = Ticket.objects.filter(order=order)

        for ticket_data in payload["tickets"]:
            exist = Ticket.objects.filter(
                seat=ticket_data["seat"],
                row=ticket_data["row"],
                flight=ticket_data["flight"],
                order=order
            ).exists()
            self.assertTrue(exist, msg=f"Ticket not found in DB: {ticket_data}")
        self.assertEqual(tickets.count(), len(payload["tickets"]))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_authenticated_user_can_delete_own_order_returns_204(self):
        url = order_get_url(self.order_1)
        res = self.client.delete(url)

        self.assertFalse(Order.objects.filter(id=self.order_1.id).exists())
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_authenticated_user_deleting_order_also_deletes_tickets_returns_204(self):
        url = order_get_url(self.order_1)
        res = self.client.delete(url)

        self.assertFalse(Order.objects.filter(id=self.order_1.id).exists())
        self.assertFalse(Ticket.objects.filter(order=self.order_1).exists())
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_authenticated_user_method_put_not_allowed_for_order_returns_405(self):
        payload = {}
        res = self.client.put(ORDER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_authenticated_user_method_patch_not_allowed_for_order_returns_405(self):
        payload = {}
        res = self.client.patch(ORDER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_authenticated_user_pagination(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("next", res.data)
        self.assertIn("previous", res.data)
        self.assertIn("results", res.data)


class AuthenticatedOrderThrottlingApiTest(BaseOrderAPITest):
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
            res = self.client.get(ORDER_URL)
            self.assertNotEqual(
                res.status_code, status.HTTP_429_TOO_MANY_REQUESTS
            )
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
