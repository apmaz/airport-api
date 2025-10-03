from datetime import datetime

from django.db.models import Count, F, Prefetch

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiExample,
    extend_schema,
)

from rest_framework import mixins
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from flight.models import (
    Crew,
    Route,
    Airport,
    AirplaneType,
    Airplane,
    Flight,
    Order,
    Ticket,
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

    @extend_schema(
        request=CrewSerializer,
        responses={201: CrewSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer
        return CrewSerializer


class RouteViewSet(ModelViewSet):
    queryset = Route.objects.all().select_related("source", "destination")

    @extend_schema(
        request=RouteSerializer,
        responses=RouteSerializer,
        examples=[
            OpenApiExample(
                "Create Route Example",
                value={"source": 0, "destination": 0, "distance": 0},
                request_only=True,
            ),
            OpenApiExample(
                "Created Route Example",
                value={"id": 0, "source": 0, "destination": 0, "distance": 0},
                response_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        responses=RouteRetrieveSerializer,
        examples=[
            OpenApiExample(
                "Retrieve Route Example",
                value={
                    "id": 0,
                    "source": {
                        "id": 0,
                        "name": "string",
                        "location_city": "string",
                        "closest_big_city": "string",
                    },
                    "destination": {
                        "id": 0,
                        "name": "string",
                        "location_city": "string",
                        "closest_big_city": "string",
                    },
                    "distance": 0,
                },
                response_only=True,
            )
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=RouteSerializer,
        responses=RouteSerializer,
        examples=[
            OpenApiExample(
                "Update Route Example",
                value={"source": 0, "destination": 0, "distance": 0},
                request_only=True,
            ),
            OpenApiExample(
                "Updated Route Example",
                value={"id": 0, "source": 0, "destination": 0, "distance": 0},
                response_only=True,
            ),
        ],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=RouteSerializer,
        responses=RouteSerializer,
        examples=[
            OpenApiExample(
                "Partial update Route Example",
                value={"source": 0, "destination": 0, "distance": 0},
                request_only=True,
            ),
            OpenApiExample(
                "Partial updated Route Example",
                value={"id": 0, "source": 0, "destination": 0, "distance": 0},
                response_only=True,
            ),
        ],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

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
    queryset = Airplane.objects.all().select_related("airplane_type")
    serializer_class = AirplaneSerializer

    @extend_schema(
        request=AirplaneSerializer,
        responses=AirplaneSerializer,
        examples=[
            OpenApiExample(
                "Create Airplane Example",
                value={
                    "name": "string",
                    "rows": 0,
                    "seats_in_row": 0,
                    "airplane_type": 0,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Created Airplane Example",
                value={
                    "id": 0,
                    "name": "string",
                    "rows": 0,
                    "seats_in_row": 0,
                    "airplane_type": 0,
                },
                response_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        responses=AirplaneRetrieveSerializer,
        examples=[
            OpenApiExample(
                "Retrieve Airplane Example",
                value={
                    "id": 0,
                    "name": "string",
                    "rows": 0,
                    "seats_in_row": 0,
                    "capacity": 0,
                    "airplane_type": {
                        "id": 0,
                        "name": "string",
                    },
                },
                response_only=True,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=AirplaneSerializer,
        responses=AirplaneSerializer,
        examples=[
            OpenApiExample(
                "Update Airplane Example",
                value={
                    "name": "string",
                    "rows": 0,
                    "seats_in_row": 0,
                    "airplane_type": 0,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Updated Airplane Example",
                value={
                    "id": 0,
                    "name": "string",
                    "rows": 0,
                    "seats_in_row": 0,
                    "airplane_type": 0,
                },
                response_only=True,
            ),
        ],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=AirplaneSerializer,
        responses=AirplaneSerializer,
        examples=[
            OpenApiExample(
                "Partial update Airplane Example",
                value={
                    "name": "string",
                    "rows": 0,
                    "seats_in_row": 0,
                    "airplane_type": 0,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Partial updated Airplane Example",
                value={
                    "id": 0,
                    "name": "string",
                    "rows": 0,
                    "seats_in_row": 0,
                    "airplane_type": 0,
                },
                response_only=True,
            ),
        ],
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        if self.action == "retrieve":
            return AirplaneRetrieveSerializer
        return AirplaneSerializer


class FlightSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 10


class FlightViewSet(ModelViewSet):
    queryset = Flight.objects.all().order_by("id")
    pagination_class = FlightSetPagination

    @staticmethod
    def _params_to_ints(query_string):
        try:
            return [int(str_id) for str_id in query_string.split(",")]
        except ValueError:
            raise ValidationError({
                "flight_source":
                    "Must be in integer (ex.flight_source=2) format."
            })

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type"
        ).prefetch_related("crew")

        if self.action == "list":
            queryset = queryset.annotate(
                tickets_available=(
                    F("airplane__rows")
                    * F("airplane__seats_in_row")
                    - Count("tickets", distinct=True)
                )
            )
            flight_source = self.request.query_params.get(
                "flight_source"
            )
            flight_destination = self.request.query_params.get(
                "flight_destination"
            )
            departure_time = self.request.query_params.get(
                "departure_time"
            )
            arrival_time = self.request.query_params.get(
                "arrival_time"
            )

            if flight_source:
                flight_source = self._params_to_ints(flight_source)
                queryset = queryset.filter(route__source__id__in=flight_source)

            if flight_destination:
                flight_destination = self._params_to_ints(flight_destination)
                queryset = queryset.filter(
                    route__destination__id__in=flight_destination
                )

            if departure_time:
                try:
                    departure_time = datetime.strptime(
                        departure_time, "%Y-%m-%d-%H:%M"
                    )
                    queryset = queryset.filter(
                        departure_time__date=departure_time
                    )
                except ValueError:
                    raise ValidationError({
                        "departure_time": "Must be in YYYY-mm-dd-HH:MM format."
                    })

            if arrival_time:
                try:
                    arrival_time = datetime.strptime(
                        arrival_time, "%Y-%m-%d-%H:%M"
                    ).date()
                    queryset = queryset.filter(arrival_time__date=arrival_time)
                except ValueError:
                    raise ValidationError({
                        "arrival_time": "Must be in YYYY-mm-dd-HH:MM format."
                    })

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="flight_source",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by flight source ID "
                            "(ex., ?flight_source=1)",
            ),
            OpenApiParameter(
                name="flight_destination",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by flight destination ID "
                            "(ex., ?flight_destination=2)",
            ),
            OpenApiParameter(
                name="departure_time",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by departure time "
                    "(ex., ?departure_time=2016-09-17-10:05)"
                ),
            ),
            OpenApiParameter(
                name="arrival_time",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Filter by arrival_time "
                    "(ex., ?arrival_time=2016-09-17-10:05)"
                ),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses=FlightRetrieveSerializer,
        examples=[
            OpenApiExample(
                "Retrieve Flight Example",
                value={
                    "id": 0,
                    "route": {
                        "id": 0,
                        "source": {
                            "id": 0,
                            "name": "string",
                            "location_city": "string",
                            "closest_big_city": "string"
                        },
                        "destination": {
                            "id": 0,
                            "name": "string",
                            "location_city": "string",
                            "closest_big_city": "string"
                        },
                        "distance": 0
                    },
                    "airplane": {
                        "id": 0,
                        "name": "string",
                        "rows": 0,
                        "seats_in_row": 0,
                        "capacity": 0,
                        "airplane_type": {
                            "id": 0,
                            "name": "string"
                        }
                    },
                    "departure_time": "2025-09-25T17:45:54.583Z",
                    "arrival_time": "2025-09-25T17:45:54.583Z",
                    "crew": ["string"],
                    "tickets_available": 0,
                    "sold_tickets": [
                        {
                            "row": 0,
                            "seat": 0
                        }
                    ]
                },
                response_only=True
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
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
    GenericViewSet,
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
                        "flight__route__destination",
                    ),
                )
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        request=OrderSerializer,
        responses=OrderSerializer,
        examples=[
            OpenApiExample(
                "Create Order Example",
                value={
                    "tickets": [
                        {
                            "flight": 0,
                            "row": 0,
                            "seat": 0,
                        }
                    ]
                },
                request_only=True,
            ),
            OpenApiExample(
                "Created Order Example",
                value={
                    "id": 0,
                    "created_at": "2025-09-25T11:02:51.191Z",
                    "tickets": [
                        {
                            "id": 0,
                            "flight": 0,
                            "row": 0,
                            "seat": 0,
                        }
                    ],
                },
                response_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        responses=OrderRetrieveSerializer,
        examples=[
            OpenApiExample(
                "Retrieve Order Example",
                value={
                    "id": 0,
                    "created_at": "2025-09-25T10:53:23.816Z",
                    "tickets": [
                        {
                            "id": 0,
                            "flight": "string",
                            "airplane_type": "string",
                            "airplane_name": "string",
                            "row": 0,
                            "seat": 0,
                        }
                    ],
                },
                response_only=True,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderRetrieveSerializer
        return OrderSerializer


class TicketViewSet(ModelViewSet):
    queryset = Ticket.objects.select_related(
        "flight__airplane",
        "flight__airplane__airplane_type",
        "flight__route__source",
        "flight__route__destination",
    )
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "retrieve":
            return TicketRetrieveSerializer
        return TicketSerializer
