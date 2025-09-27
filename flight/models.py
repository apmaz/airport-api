import pathlib
import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from airport_api import settings


class Flight(models.Model):
    route = models.ForeignKey(
        "Route", on_delete=models.CASCADE, related_name="flights"
    )
    airplane = models.ForeignKey(
        "Airplane", on_delete=models.CASCADE, related_name="flights"
    )
    crew = models.ManyToManyField("Crew", related_name="flights", blank=False)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["departure_time"]),
            models.Index(fields=["arrival_time"]),
            models.Index(fields=["route"]),
        ]

    @property
    def flight_info(self) -> str:
        return (
            f"{self.route.source.location_city} -> "
            f"{self.route.destination.location_city}"
        )

    def clean(self):
        super().clean()
        if self.departure_time >= self.arrival_time:
            raise ValidationError("Departure_time must be before arrival_time")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Flight: {self.route.source.location_city} -> "
            f"{self.route.destination.location_city} "
            f"{self.departure_time} - {self.arrival_time}"
        )


class Route(models.Model):
    source = models.ForeignKey(
        "Airport", on_delete=models.CASCADE, related_name="routes_from"
    )
    destination = models.ForeignKey(
        "Airport", on_delete=models.CASCADE, related_name="routes_to"
    )
    distance = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        indexes = [
            models.Index(fields=["source", "destination"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "destination"],
                name="unique_source_destination",
            )
        ]

    @property
    def source_to_destination(self) -> str:
        return (
            f"{self.source.location_city} -> "
            f"{self.destination.location_city}"
        )

    def clean(self):
        super().clean()
        if self.source == self.destination:
            raise ValidationError("Source and destination must be different")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return \
            (f"{self.source.location_city} -> "
             f"{self.destination.location_city}")


class Airplane(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rows = models.IntegerField(validators=[MinValueValidator(1)])
    seats_in_row = models.IntegerField(validators=[MinValueValidator(1)])
    airplane_type = models.ForeignKey(
        "AirplaneType", on_delete=models.CASCADE, related_name="airplanes"
    )

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.airplane_type.name} ({self.name})"


def crew_image_upload_path(instance: "Crew", filename: str) -> pathlib.Path:
    filename = (
        f"{slugify(instance.full_name)}--{uuid.uuid4()}"
        + pathlib.Path(filename).suffix
    )
    return pathlib.Path("uploads/crew/") / pathlib.Path(filename)


class Crew(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    crew_photo = models.ImageField(
        null=True, upload_to=crew_image_upload_path
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class Airport(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location_city = models.CharField(max_length=100)
    closest_big_city = models.CharField(
        max_length=100, unique=False, null=True, blank=True
    )

    def __str__(self):
        return f"{self.name} (location city: {self.location_city})"


class AirplaneType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        "Flight", on_delete=models.CASCADE, related_name="tickets"
    )
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, related_name="tickets"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["flight", "row", "seat"],
                name="unique_flight_row_seat",
            ),
        ]

    @staticmethod
    def validate_ticket(row, seat, airplane, type_error):
        to_rise = {}

        for value, name, limit in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            max_val = getattr(airplane, limit)
            if not (1 <= value <= max_val):
                to_rise[limit] = f"{name} must be between 1 and {max_val}"

        if to_rise:
            raise type_error(to_rise)

    def clean(self):
        self.validate_ticket(
            self.row, self.seat, self.flight.airplane, ValidationError
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Ticket: {self.row} {self.seat} "
            f"{self.flight.airplane} {self.order.id}"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order: {self.user} {self.created_at}"
