"""Django application configuration for the users app."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Application metadata."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
