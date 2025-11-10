"""Admin configuration for the custom user model."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Display and manage users in the admin site."""

    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "user_type",
        "linked_professional",
        "is_staff",
        "is_active",
    )
    list_filter = ("user_type", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "user_type",
                    "linked_professional",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "user_type",
                    "linked_professional",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
    )
