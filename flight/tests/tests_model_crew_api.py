from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APIClient

from flight.models import Crew
from flight.serializers import CrewSerializer, CrewListSerializer


CREW_URL = reverse("flight:crew-list")


def crew_get_url(crew) -> str:
    return reverse("flight:crew-detail", args=[crew.id])


def sample_crew(**kwargs) -> Crew:
    defaults = {
        "first_name": "Peter",
        "last_name": "Jefferson",
    }
    defaults.update(**kwargs)
    return Crew.objects.create(**defaults)


class BaseCrewAPITest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.crew_1 = sample_crew()
        self.crew_2 = sample_crew(
            first_name="Alex",
            last_name="Anderson",
        )


class UnauthenticatedCrewApiTest(BaseCrewAPITest):
    def setUp(self):
        super().setUp()

    def test_unauthenticated_user_crew_list_returns_401(self):
        res = self.client.get(CREW_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_crew_retrieve_returns_401(self):
        url = crew_get_url(self.crew_1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_crew_returns_401(self):
        payload = {
            "first_name": "Derry",
            "last_name": "Smith",
        }
        res = self.client.post(CREW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_patch_crew_returns_401(self):
        url = crew_get_url(self.crew_1)
        payload = {"first_name": "Derry"}
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_put_crew_returns_401(self):
        url = crew_get_url(self.crew_1)
        payload = {
            "first_name": "Derry",
            "last_name": "Smith",
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_delete_crew_returns_401(self):
        url = crew_get_url(self.crew_1)
        res = self.client.delete(url)
        self.assertTrue(
            Crew.objects.filter(id=self.crew_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewApiTest(BaseCrewAPITest):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_crew_list_returns_200(self):
        res = self.client.get(CREW_URL)
        crews = Crew.objects.all()
        serializer = CrewListSerializer(crews, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_authenticated_user_crew_retrieve_returns_200(self):
        url = crew_get_url(self.crew_1)
        res = self.client.get(url)
        serializer = CrewSerializer(self.crew_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_authenticated_user_cannot_create_crew_returns_403(self):
        payload = {
            "first_name": "Derry",
            "last_name": "Smith",
        }
        res = self.client.post(CREW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_patch_crew_returns_403(self):
        url = crew_get_url(self.crew_1)
        payload = {"first_name": "Derry"}
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_put_crew_returns_403(self):
        url = crew_get_url(self.crew_1)
        payload = {
            "first_name": "Derry",
            "last_name": "Smith",
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_cannot_delete_crew_returns_403(self):
        url = crew_get_url(self.crew_1)
        res = self.client.delete(url)
        self.assertTrue(
            Crew.objects.filter(id=self.crew_1.id).exists()
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_pagination(self):
        res = self.client.get(CREW_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("count", res.data)
        self.assertIn("next", res.data)
        self.assertIn("previous", res.data)
        self.assertIn("results", res.data)


class AuthenticatedCrewThrottlingApiTest(BaseCrewAPITest):
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
            res = self.client.get(CREW_URL)
            self.assertNotEqual(
                res.status_code, status.HTTP_429_TOO_MANY_REQUESTS
            )
        res = self.client.get(CREW_URL)
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AdminCrewApiTest(BaseCrewAPITest):
    def setUp(self):
        super().setUp()
        self.admin = get_user_model().objects.create_user(
            email="admin@test.com",
            password="password",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin)

    def test_admin_crew_list_returns_200(self):
        res = self.client.get(CREW_URL)
        crews = Crew.objects.all()
        serializer = CrewListSerializer(crews, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_admin_crew_retrieve_returns_200(self):
        url = crew_get_url(self.crew_1)
        res = self.client.get(url)
        serializer = CrewSerializer(self.crew_1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_admin_create_crew_returns_201(self):
        payload = {
            "first_name": "Derry",
            "last_name": "Smith",
        }
        res = self.client.post(CREW_URL, payload)
        crew = Crew.objects.get(id=res.data["id"])
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(crew, key))

    def test_admin_create_crew_without_first_name_returns_400(self):
        payload = {
            "first_name": "",
            "last_name": "Smith",
        }
        res = self.client.post(CREW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_create_crew_without_last_name_returns_400(self):
        payload = {
            "first_name": "Derry",
            "last_name": "",
        }
        res = self.client.post(CREW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_patch_crew_returns_200(self):
        url = crew_get_url(self.crew_1)
        payload = {"first_name": "Derry"}
        res = self.client.patch(url, payload)
        self.crew_1.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["first_name"], self.crew_1.first_name)

    def test_admin_put_crew_returns_200(self):
        url = crew_get_url(self.crew_1)
        payload = {
            "first_name": "Derry",
            "last_name": "Smith",
        }
        res = self.client.put(url, payload)
        self.crew_1.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key in payload:
            self.assertEqual(payload[key], getattr(self.crew_1, key))

    def test_admin_delete_crew_returns_204(self):
        url = crew_get_url(self.crew_1)
        res = self.client.delete(url)
        self.assertFalse(
            Crew.objects.filter(id=self.crew_1.id).exists(),
            msg=f"Crew {self.crew_1.id} was not deleted"
        )
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
