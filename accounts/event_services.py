"""Business logic for creating and deleting calendar events.

Extracted from views to keep handlers thin and testable.
"""
from datetime import datetime, timedelta

from django.utils import timezone

from .models import Event, EventAttendee, Service
from django.contrib.auth import get_user_model

User = get_user_model()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())

    naive_local = parsed.replace(tzinfo=None)
    return timezone.make_aware(naive_local, timezone.get_current_timezone())


def create_event(user: User, calendar, start_at_raw: str, end_at_raw: str, service_id, client_id):
    """Create an Event and EventAttendee if valid.

    Returns (True, event) on success or (False, message) on failure.
    """
    if not calendar:
        return False, "Calendrier introuvable."
    start_at = _parse_iso_datetime(start_at_raw)
    if start_at is None:
        return False, "Date de début invalide."
    end_at = _parse_iso_datetime(end_at_raw)
    if end_at is None:
        end_at = start_at

    service = Service.objects.filter(pk=service_id, created_by=user).first()
    client = User.objects.filter(
        pk=client_id,
        linked_professional=user,
        user_type=User.UserType.INDIVIDUAL,
    ).first()
    if not (service and client):
        return False, "Prestation ou client invalide."

    if end_at <= start_at:
        duration = service.duration_minutes or 60
        end_at = start_at + timedelta(minutes=duration)

    event = Event.objects.create(
        calendar=calendar,
        title=service.name,
        description=service.description or "",
        start_at=start_at,
        end_at=end_at,
        created_by=user,
        status="planned",
    )
    EventAttendee.objects.create(event=event, user=client)
    return True, event


def delete_event(user: User, event_id):
    """Delete an event owned by the user's calendar.

    Returns (True, None) on success or (False, message) on failure.
    """
    event = (
        Event.objects.select_related("calendar", "calendar__owner")
        .filter(pk=event_id, calendar__owner=user)
        .first()
    )
    if not event:
        return False, "Rendez-vous introuvable ou non autorisé."
    event.delete()
    return True, None
