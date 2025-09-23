from django.db import transaction
from rest_framework import serializers

from flight.models import (
    Crew,
    Airplane,
    AirplaneType,
    Airport,
    Route,
    Flight,
    Order,
    Ticket
)


class CrewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "crew_photo",)


class CrewListSerializer(serializers.ModelSerializer):
    full_name = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Crew
        fields = ("id", "full_name", "crew_photo",)


class AirportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airport
        fields = ("id", "name", "location_city", "closest_big_city",)


class RouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance",)


class RouteListSerializer(serializers.ModelSerializer):
    route_info = serializers.CharField(
        read_only=True, source="source_to_destination"
    )

    class Meta:
        model = Route
        fields = ("id", "route_info",)


class RouteRetrieveSerializer(serializers.ModelSerializer):
    source = AirportSerializer(read_only=True)
    destination = AirportSerializer(read_only=True)

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance",)


class AirplaneTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AirplaneType
        fields = ("id", "name",)


class AirplaneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
        )


class AirplaneListSerializer(serializers.ModelSerializer):
    airplane_type = serializers.SlugRelatedField(
        slug_field="name",
        read_only=True
    )

    class Meta:
        model = Airplane
        fields = ("id", "name", "airplane_type",)


class AirplaneRetrieveSerializer(serializers.ModelSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "capacity",
            "airplane_type",
        )


class FlightSerializer(serializers.ModelSerializer):

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
        )


class FlightListSerializer(serializers.ModelSerializer):
    route = serializers.StringRelatedField(read_only=True)
    airplane = serializers.StringRelatedField(read_only=True)
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "tickets_available",
            "airplane",
        )


class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("id", "flight", "row", "seat",)

    def validate(self, attrs):
        airplane = attrs["flight"].airplane
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            airplane,
            type_error=serializers.ValidationError
        )

        return attrs


class TicketListSerializer(serializers.ModelSerializer):
    flight = serializers.SlugRelatedField(
        read_only=True, slug_field="flight_info"
    )
    departure_time = serializers.CharField(
        read_only=True, source="flight.departure_time"
    )
    arrival_time = serializers.CharField(
        read_only=True, source="flight.arrival_time"
    )

    class Meta:
        model = Ticket
        fields = (
            "id",
            "flight",
            "departure_time",
            "arrival_time",
        )


class TicketRetrieveSerializer(serializers.ModelSerializer):
    flight = serializers.ReadOnlyField(
        source="flight.flight_info", read_only=True
    )
    airplane_name = serializers.CharField(
        source="flight.airplane.name",
        read_only=True
    )
    airplane_type = serializers.CharField(
        source="flight.airplane.airplane_type.name",
        read_only = True
    )

    class Meta:
        model = Ticket
        fields = (
            "id",
            "flight",
            "airplane_type",
            "airplane_name",
            "row",
            "seat",
        )

class TicketShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("row", "seat",)


class FlightRetrieveSerializer(serializers.ModelSerializer):
    route = RouteRetrieveSerializer(
        read_only=True, many=False
    )
    airplane = AirplaneRetrieveSerializer(
        read_only=True, many=False
    )
    crew = serializers.SlugRelatedField(
        read_only=True, many=True, slug_field="full_name"
    )
    tickets_available = serializers.IntegerField(read_only=True)
    sold_tickets = TicketShortSerializer(
        many=True, read_only=True, source="tickets"
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew",
            "tickets_available",
            "sold_tickets",
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        read_only=False,
        allow_empty = False
    )

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets",)

    def create(self, validated_data):
        with transaction.atomic():
            tickets = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket in tickets:
                Ticket.objects.create(order=order, **ticket)

            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)


class OrderRetrieveSerializer(OrderSerializer):
    tickets = TicketRetrieveSerializer(many=True, read_only=True)
