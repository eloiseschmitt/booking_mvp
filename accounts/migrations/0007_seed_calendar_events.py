"""Seed planning data with sample calendar events."""

# pylint: disable=invalid-name

from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils import timezone


SAMPLE_EVENTS = [
    # weekday, start, end, first_name, last_name, email, service_name
    (
        0,
        "09:00",
        "10:05",
        "Camille",
        "Thomas",
        "camille.thomas@example.com",
        "Modelage bien-être",
    ),
    (
        0,
        "11:30",
        "12:30",
        "Valérie",
        "Dupont",
        "valerie.dupont@example.com",
        "Soin découverte",
    ),
    (
        0,
        "14:00",
        "15:20",
        "Valérie",
        "Dupont",
        "valerie.dupont@example.com",
        "Soin corps complet",
    ),
    (
        0,
        "17:00",
        "17:55",
        "Jackie",
        "Vernhères",
        "jackie.vernhere@example.com",
        "Massage relaxant",
    ),
    (
        1,
        "09:40",
        "10:35",
        "Laetitia",
        "Martin",
        "laetitia.martin@example.com",
        "Kobido visage",
    ),
    (
        1,
        "12:30",
        "13:30",
        "Valérie",
        "Dupont",
        "valerie.dupont@example.com",
        "Séance entreprise",
    ),
    (
        1,
        "14:00",
        "14:45",
        "Prate",
        "Michelle",
        "prate.michelle@example.com",
        "Massage express",
    ),
    (
        2,
        "09:00",
        "14:00",
        "Equipe",
        "Interne",
        "formation@kitlast.test",
        "Bloc formation interne",
    ),
    (
        3,
        "09:15",
        "09:45",
        "Manon",
        "Leroy",
        "manon.leroy@example.com",
        "Mise en beauté",
    ),
    (
        3,
        "11:15",
        "12:15",
        "Danny",
        "Rossi",
        "danny.rossi@example.com",
        "Soin éclat intense",
    ),
    (
        3,
        "14:15",
        "15:20",
        "Sarah",
        "Benoit",
        "sarah.benoit@example.com",
        "Modelage signature",
    ),
    (
        3,
        "17:00",
        "17:45",
        "Isabelle",
        "Garnier",
        "isabelle.garnier@example.com",
        "Rehaussement de cils",
    ),
    (
        4,
        "09:00",
        "09:35",
        "Séverine",
        "Lopez",
        "severine.lopez@example.com",
        "Pose vernis",
    ),
    (
        4,
        "11:00",
        "12:00",
        "Sabrina",
        "Moreau",
        "sabrina.moreau@example.com",
        "Forfait duo",
    ),
    (
        4,
        "18:00",
        "18:25",
        "Laure",
        "Cousin",
        "laure.cousin@example.com",
        "Conseils personnalisés",
    ),
    (
        5,
        "09:00",
        "10:30",
        "Equipe",
        "Collectif",
        "atelier.collectif@kitlast.test",
        "Coaching maquillage",
    ),
    (
        5,
        "14:00",
        "15:30",
        "Equipe",
        "Collectif",
        "atelier.collectif@kitlast.test",
        "Atelier collectif",
    ),
]

CATEGORY_NAME = "Prestations planning"
CALENDAR_SLUG = "planning-hebdomadaire"


def _get_or_create_user(user_model, email: str, first_name: str, last_name: str):
    defaults = {
        "first_name": first_name,
        "last_name": last_name,
        "user_type": "professional",
        "is_active": True,
    }
    user = user_model.objects.filter(email=email).first()
    if user:
        update_fields = []
        for field, value in defaults.items():
            if getattr(user, field, None) != value:
                setattr(user, field, value)
                update_fields.append(field)
        if update_fields:
            user.save(update_fields=update_fields)
        return user

    password_hash = make_password("kitlast123")
    return user_model.objects.create(password=password_hash, email=email, **defaults)


def _parse_time(base_date, weekday: int, time_str: str):
    target_date = base_date + timedelta(days=weekday)
    hour, minute = map(int, time_str.split(":"))
    naive = datetime(target_date.year, target_date.month, target_date.day, hour, minute)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def create_events(apps, _schema_editor):  # pylint: disable=too-many-locals
    """Populate the planning tables with sample data."""

    user_model = apps.get_model("users", "User")
    category_model = apps.get_model("accounts", "Category")
    service_model = apps.get_model("accounts", "Service")
    calendar_model = apps.get_model("accounts", "Calendar")
    event_model = apps.get_model("accounts", "Event")
    attendee_model = apps.get_model("accounts", "EventAttendee")

    owner = _get_or_create_user(
        user_model, "planner@kitlast.test", "Planning", "Manager"
    )

    calendar, created = calendar_model.objects.get_or_create(
        owner=owner,
        slug=CALENDAR_SLUG,
        defaults={"name": "Planning hebdomadaire", "is_public": True},
    )
    if not created and not calendar.is_public:
        calendar.is_public = True
        calendar.save(update_fields=["is_public"])

    category, _ = category_model.objects.get_or_create(name=CATEGORY_NAME)

    services_cache = {}
    for _, _, _, _, _, _, service_name in SAMPLE_EVENTS:
        service = service_model.objects.filter(name=service_name).first()
        if service is None:
            service = service_model.objects.create(
                category=category,
                name=service_name,
                created_by=owner,
            )
        services_cache[service_name] = service

    base_date = timezone.localdate()
    base_date = base_date - timedelta(days=base_date.weekday())

    for index, (weekday, start, end, first, last, email, service_name) in enumerate(
        SAMPLE_EVENTS
    ):
        attendee = _get_or_create_user(user_model, email, first, last)
        service = services_cache[service_name]
        start_at = _parse_time(base_date, weekday, start)
        end_at = _parse_time(base_date, weekday, end)

        event, _ = event_model.objects.update_or_create(
            calendar=calendar,
            start_at=start_at,
            end_at=end_at,
            title=service.name,
            defaults={
                "description": service.description,
                "created_by": attendee,
                "status": "confirmed" if index % 3 == 0 else "planned",
            },
        )

        attendee_model.objects.get_or_create(
            event=event,
            user=attendee,
            defaults={"role": "owner", "is_confirmed": True},
        )

        attendee_model.objects.get_or_create(
            event=event,
            user=owner,
            defaults={"role": "owner", "is_confirmed": True},
        )


def delete_events(apps, _schema_editor):
    """Rollback helper to remove seeded data."""

    calendar_model = apps.get_model("accounts", "Calendar")
    try:
        calendar = calendar_model.objects.get(slug=CALENDAR_SLUG)
    except calendar_model.DoesNotExist:
        return
    calendar.events.all().delete()
    calendar.delete()


class Migration(migrations.Migration):
    """Seed the planning calendar with fixtures."""

    dependencies = [
        ("accounts", "0006_calendar_event_eventattendee"),
        ("users", "0002_user_user_type"),
    ]

    operations = [
        migrations.RunPython(create_events, delete_events),
    ]
