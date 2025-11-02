"""Database models for the accounts application."""

from django.conf import settings
from django.db import models


class Category(models.Model):
    """A simple grouping to organise services."""

    # pylint: disable=too-few-public-methods
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Default ordering for categories."""

        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)


class Service(models.Model):
    """A service that can be delivered as part of a workshop portfolio."""

    # pylint: disable=too-few-public-methods
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="services"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="services_created",
    )

    class Meta:
        """Default ordering for services."""

        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)


class Workshop(models.Model):
    """A physical workshop where services are delivered."""

    # pylint: disable=too-few-public-methods
    name = models.CharField(max_length=150)
    address = models.TextField()
    zip_code = models.CharField(max_length=10)
    city = models.CharField(max_length=150)
    photo = models.CharField(max_length=255, blank=True)
    services = models.ManyToManyField(Service, related_name="workshops", blank=True)
    professionals = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="professional_workshops",
        blank=True,
        limit_choices_to={"user_type": "professional"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Default ordering for workshops."""

        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)


class Calendar(models.Model):
    """Personal agenda owned by a single user."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendars",
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("owner", "slug")
        ordering = ["owner__id", "name"]
        verbose_name = "calendar"
        verbose_name_plural = "calendars"

    def __str__(self):
        return f"{self.name} ({self.owner})"


class Event(models.Model):
    """Single calendar entry scheduled for a time range."""

    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        related_name="events",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    status = models.CharField(
        max_length=30,
        choices=(
            ("planned", "Planned"),
            ("confirmed", "Confirmed"),
            ("canceled", "Canceled"),
        ),
        default="planned",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_events",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at"]
        verbose_name = "event"
        verbose_name_plural = "events"

    def __str__(self):
        return f"{self.title} – {self.start_at} → {self.end_at}"


class EventAttendee(models.Model):
    """Association between an event and a participant."""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="attendees",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=30,
        choices=(
            ("owner", "Owner"),
            ("required", "Required"),
            ("optional", "Optional"),
        ),
        default="required",
    )
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("event", "user")
        verbose_name = "event attendee"
        verbose_name_plural = "event attendees"
