"""Planning helpers used to build calendar views in the dashboard."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from django.utils import timezone

from .constants import (
    FALLBACK_WEEK,
    PLANNER_COLOR_PALETTE,
    TOTAL_PLANNER_SPAN_MINUTES,
)
from .event_view import EventView
from .models import Calendar, Service


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


def _fallback_sample_week() -> list[dict[str, object]]:
    base_year = timezone.localdate().year
    fallback: list[dict[str, object]] = []
    for label, date_label, events in FALLBACK_WEEK:
        day_events: list[dict[str, object]] = []
        for start, end, service_name, person, color in events:
            start_dt = datetime.strptime(f"{date_label}/{base_year} {start}", "%d/%m/%Y %H:%M")
            end_dt = datetime.strptime(f"{date_label}/{base_year} {end}", "%d/%m/%Y %H:%M")
            start_iso = timezone.make_aware(start_dt, timezone.get_current_timezone()).isoformat()
            end_iso = timezone.make_aware(end_dt, timezone.get_current_timezone()).isoformat()
            day_events.append(
                {
                    "time": f"{start} – {end}",
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


def _empty_week() -> list[dict[str, object]]:
    return [{"label": label, "date": date_label, "events": []} for label, date_label, _ in FALLBACK_WEEK]


def build_calendar_events(calendar: Calendar | None) -> list[dict[str, object]]:
    """Generate planner data either from the database or fallback sample data."""

    if calendar is None:
        return SAMPLE_WEEK

    events_by_day: dict[tuple[str, str], list[EventView]] = defaultdict(list)
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
            EventView(
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
        return _empty_week()

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
