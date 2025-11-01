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
