from django.urls import include, path
from rest_framework import routers

from flight.views import (
    CrewViewSet,
    RouteViewSet,
    AirportViewSet,
    AirplaneTypeViewSet,
    AirplaneViewSet,
    FlightViewSet,
    OrderViewSet
)


app_name = "flight"

router = routers.DefaultRouter()

router.register("crews", CrewViewSet, basename="crew")
router.register("routes", RouteViewSet, basename="route")
router.register("airports", AirportViewSet, basename="airport")
router.register("airplane-types", AirplaneTypeViewSet, basename="airplane-type")
router.register("airplanes", AirplaneViewSet, basename="airplane")
router.register("flights", FlightViewSet, basename="flight")
router.register("orders", OrderViewSet, basename="order")


urlpatterns = [path("", include(router.urls))]
