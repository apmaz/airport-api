from django.db.models import Count, F, Prefetch
from rest_framework import mixins
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


class FlightViewSet(ModelViewSet):
    queryset = Flight.objects.all()

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
        elif self.action == "retrieve":
            queryset = queryset

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):

    queryset = Order.objects.all()

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

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        elif self.action == "retrieve":
            return TicketRetrieveSerializer
        return TicketSerializer
