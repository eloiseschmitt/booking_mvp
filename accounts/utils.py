"""Utility helpers for accounts app."""

from django.utils.text import slugify

from .models import Calendar


def ensure_user_calendar(user):
    """Return the calendar for a user, creating it if needed."""
    calendar = Calendar.objects.filter(owner=user).first()
    if calendar is None:
        calendar = Calendar.objects.filter(is_public=True).first()
    if calendar is not None:
        return calendar

    base_slug = slugify(f"agenda-{user.pk}") or f"agenda-{user.pk}"
    slug = base_slug
    suffix = 1
    while Calendar.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    return Calendar.objects.create(
        owner=user,
        name=f"Agenda de {user.first_name or user.email}",
        slug=slug,
    )
