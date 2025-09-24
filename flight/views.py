from datetime import datetime

from django.db.models import Count, F, Prefetch
from rest_framework import mixins
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from flight.models import (
    Crew,
    Route,
    Airport,
    AirplaneType,
    Airplane,
    Flight,
    Order,
    Ticket
)
from flight.serializers import (
    CrewSerializer,
    CrewListSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    AirportSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneRetrieveSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightRetrieveSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderRetrieveSerializer,
    TicketSerializer,
    TicketRetrieveSerializer,
    TicketListSerializer,
)


class CrewViewSet(ModelViewSet):
    queryset = Crew.objects.all()

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer
        return CrewSerializer


class RouteViewSet(ModelViewSet):
    queryset = Route.objects.all().select_related(
        "source",
        "destination"
    )

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteRetrieveSerializer
        return RouteSerializer


class AirportViewSet(ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class AirplaneTypeViewSet(ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(ModelViewSet):
    queryset = Airplane.objects.all().select_related(
        "airplane_type"
    )
    serializer_class = AirplaneSerializer


    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        elif self.action == "retrieve":
            return AirplaneRetrieveSerializer
        return AirplaneSerializer


class FlightSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 10


class FlightViewSet(ModelViewSet):
    queryset = Flight.objects.all()
    pagination_class = FlightSetPagination

    @staticmethod
    def _params_to_ints(query_string):
        try:
            return [int(str_id) for str_id in query_string.split(',')]
        except ValueError:
            raise ValidationError(
                {
                    "flight_source": "Must be in integer (ex.flight_source=2) format."
                }
            )

    def get_queryset(self):
        queryset = (super().get_queryset().select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type").prefetch_related("crew")
                    )

        if self.action == "list":
            queryset = (
                queryset.annotate(
                    tickets_available=
                    F("airplane__rows") * F("airplane__seats_in_row") -
                    Count("tickets", distinct=True)
                )
            )

            flight_source = self.request.query_params.get("flight_source")
            flight_destination = self.request.query_params.get("flight_destination")
            departure_time = self.request.query_params.get("departure_time")
            arrival_time = self.request.query_params.get("arrival_time")

            if flight_source:
                flight_source = self._params_to_ints(flight_source)
                queryset = queryset.filter(route__source__id__in=flight_source)

            if flight_destination:
                flight_destination = self._params_to_ints(flight_destination)
                queryset = queryset.filter(route__destination__id__in=flight_destination)

            if departure_time:
                try:
                    departure_time = datetime.strptime(
                        departure_time, "%Y-%m-%d-%H:%M"
                    )
                    queryset = queryset.filter(
                        departure_time__date=departure_time
                    )
                except ValueError:
                    raise ValidationError(
                        {"departure_time": "Must be in YYYY-mm-dd-HH:MM format."}
                    )

            if arrival_time:
                try:
                    arrival_time = datetime.strptime(
                        arrival_time, "%Y-%m-%d-%H:%M"
                    ).date()
                    queryset = queryset.filter(arrival_time__date=arrival_time)
                except ValueError:
                    raise ValidationError(
                        {"arrival_time": "Must be in YYYY-mm-dd-HH:MM format."}
                    )

        elif self.action == "retrieve":
            queryset = queryset

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer


class OrderSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 10


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):

    queryset = Order.objects.all()
    permission_classes = (IsAuthenticated,)
    pagination_class = OrderSetPagination

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("user").prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "flight__airplane",
                        "flight__airplane__airplane_type",
                        "flight__route__source",
                        "flight__route__destination"
                    )
                )
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "retrieve":
            return OrderRetrieveSerializer
        return OrderSerializer


class TicketViewSet(ModelViewSet):
    queryset = Ticket.objects.select_related(
        "flight__airplane",
        "flight__airplane__airplane_type",
        "flight__route__source",
        "flight__route__destination"
    )
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        elif self.action == "retrieve":
            return TicketRetrieveSerializer
        return TicketSerializer
