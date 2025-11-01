"""Django application configuration for the accounts app."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Application metadata."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
