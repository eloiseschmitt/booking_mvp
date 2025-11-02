"""Planning helpers used to build calendar views in the dashboard."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import NamedTuple

from django.utils import timezone

from .constants import (
    PLANNER_COLOR_PALETTE,
    PLANNER_HOURS as _PLANNER_HOURS,
    TOTAL_PLANNER_SPAN_MINUTES,
)
from .models import Calendar, Service


PLANNER_HOURS = _PLANNER_HOURS


class _EventView(NamedTuple):
    label: str
    date: str
    time: str
    title: str
    color: str
    service: str
    category: str
    description: str
    status: str
    created_by: str
    start: str
    end: str
    top_pct: float
    height_pct: float


def _to_minutes(value: str | datetime) -> int:
    if isinstance(value, datetime):
        return value.hour * 60 + value.minute
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def _compute_block(start_time: str | datetime, end_time: str | datetime) -> dict[str, float]:
    start_minutes = _to_minutes(start_time)
    end_minutes = _to_minutes(end_time)
    top = max(start_minutes - 8 * 60, 0)
    duration = max(end_minutes - start_minutes, 30)
    return {
        "top_pct": (top / TOTAL_PLANNER_SPAN_MINUTES) * 100,
        "height_pct": (duration / TOTAL_PLANNER_SPAN_MINUTES) * 100,
    }


def _format_time_range(start_time: datetime, end_time: datetime) -> str:
    return f"{start_time.strftime('%H:%M')} – {end_time.strftime('%H:%M')}"


def _weekday_label(value: datetime) -> str:
    return ["Lun.", "Mar.", "Mer.", "Jeu.", "Ven.", "Sam.", "Dim."][value.weekday()]


_BASE_SAMPLE_WEEK = [
    (
        "Lun.",
        "15/09",
        [
            ("09:00", "10:05", "Modelage bien-être", "Camille Thomas", "#7C8FF8"),
            ("11:30", "12:30", "Soin découverte", "Valérie", "#E07B39"),
            ("14:00", "15:20", "Soin corps complet", "Valérie", "#6BC0A5"),
            ("17:00", "17:55", "Modelage", "Jackie Vernhères", "#AF77E5"),
        ],
    ),
    (
        "Mar.",
        "16/09",
        [
            ("09:40", "10:35", "Kobido visage", "Laetitia", "#2CB7C6"),
            ("12:30", "13:30", "Séance entreprise", "Valérie", "#A7B0C0"),
            ("14:00", "14:45", "Massage express", "Prate Michelle", "#F06FA7"),
        ],
    ),
    (
        "Mer.",
        "17/09",
        [
            ("09:00", "14:00", "Bloc formation interne", "Équipe interne", "#D1D7E0"),
        ],
    ),
    (
        "Jeu.",
        "18/09",
        [
            ("09:15", "09:45", "Mise en beauté", "Manon", "#4AC07A"),
            ("11:15", "12:15", "Soin éclat intense", "Danny", "#5272FF"),
            ("14:15", "15:20", "Modelage signature", "Sarah B.", "#AF77E5"),
            ("17:00", "17:45", "Rehaussement de cils", "Isabelle", "#FFB347"),
        ],
    ),
    (
        "Ven.",
        "19/09",
        [
            ("09:00", "09:35", "Pose vernis", "Séverine", "#4AC07A"),
            ("11:00", "12:00", "Forfait duo", "Sabrina", "#E07B39"),
            ("18:00", "18:25", "Conseils personnalisés", "Laure", "#F06FA7"),
        ],
    ),
    (
        "Sam.",
        "20/09",
        [
            ("09:00", "10:30", "Coaching maquillage", "Equipe collectif", "#7C8FF8"),
            ("14:00", "15:30", "Atelier collectif", "Equipe collectif", "#6BC0A5"),
        ],
    ),
    ("Dim.", "21/09", []),
]


def _fallback_sample_week() -> list[dict[str, object]]:
    base_year = timezone.localdate().year
    fallback: list[dict[str, object]] = []
    for label, date_label, events in _BASE_SAMPLE_WEEK:
        day_events: list[dict[str, object]] = []
        for start, end, service_name, person, color in events:
            time_display = f"{start} – {end}"
            start_dt = datetime.strptime(f"{date_label}/{base_year} {start}", "%d/%m/%Y %H:%M")
            end_dt = datetime.strptime(f"{date_label}/{base_year} {end}", "%d/%m/%Y %H:%M")
            start_iso = timezone.make_aware(start_dt, timezone.get_current_timezone()).isoformat()
            end_iso = timezone.make_aware(end_dt, timezone.get_current_timezone()).isoformat()
            day_events.append(
                {
                    "time": time_display,
                    "title": f"{person} · {service_name}",
                    "service": service_name,
                    "category": "",
                    "description": "",
                    "status": "Planifié",
                    "created_by": person,
                    "start": start_iso,
                    "end": end_iso,
                    "color": color,
                    **_compute_block(start, end),
                }
            )
        fallback.append({"label": label, "date": date_label, "events": day_events})
    return fallback


def build_calendar_events(calendar: Calendar | None) -> list[dict[str, object]]:
    """Generate planner data either from the database or fallback sample data."""

    if calendar is None:
        return SAMPLE_WEEK

    events_by_day: dict[tuple[str, str], list[_EventView]] = defaultdict(list)
    queryset = list(calendar.events.select_related("created_by").order_by("start_at"))
    titles = {event.title for event in queryset}
    service_lookup = {
        service.name: service
        for service in Service.objects.filter(name__in=titles).select_related("category")
    }

    for index, event in enumerate(queryset):
        start_local = timezone.localtime(event.start_at)
        end_local = timezone.localtime(event.end_at)
        label = _weekday_label(start_local)
        date_label = start_local.strftime("%d/%m")
        color = PLANNER_COLOR_PALETTE[index % len(PLANNER_COLOR_PALETTE)]

        service_model = service_lookup.get(event.title)
        service_name = service_model.name if service_model else event.title
        category_name = service_model.category.name if service_model and service_model.category else ""

        author = ""
        if event.created_by:
            author_parts = [
                getattr(event.created_by, "first_name", "") or "",
                getattr(event.created_by, "last_name", "") or "",
            ]
            author = " ".join(part for part in author_parts if part).strip() or event.created_by.email

        display_title = f"{author} · {service_name}" if author else service_name

        events_by_day[label, date_label].append(
            _EventView(
                label=label,
                date=date_label,
                time=_format_time_range(start_local, end_local),
                title=display_title,
                color=color,
                service=service_name,
                category=category_name,
                description=event.description or "",
                status=event.get_status_display(),
                created_by=author,
                start=start_local.isoformat(),
                end=end_local.isoformat(),
                **_compute_block(start_local, end_local),
            )
        )

    if not events_by_day:
        return SAMPLE_WEEK

    grouped: list[dict[str, object]] = []
    for (label, date_label), events in sorted(
        events_by_day.items(), key=lambda item: datetime.strptime(item[0][1], "%d/%m")
    ):
        grouped.append(
            {
                "label": label,
                "date": date_label,
                "events": [event._asdict() for event in events],
            }
        )

    return grouped


SAMPLE_WEEK = _fallback_sample_week()
