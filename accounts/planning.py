"""Planning helpers used to build calendar views in the dashboard."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from .constants import (
    FALLBACK_WEEK,
    PLANNER_COLOR_PALETTE,
    PLANNER_HOURS as _PLANNER_HOURS,
    TOTAL_PLANNER_SPAN_MINUTES,
)
from .event_view import EventView
from .models import Calendar, Service

PLANNER_HOURS = _PLANNER_HOURS


def _to_minutes(value: str | datetime) -> int:
    if isinstance(value, datetime):
        return value.hour * 60 + value.minute
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def _compute_block(
    start_time: str | datetime, end_time: str | datetime
) -> dict[str, float]:
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


def _start_of_week(week_offset: int) -> date:
    """Return the date for the Monday of the requested week offset."""

    today = timezone.localdate()
    current_week_start = today - timedelta(days=today.weekday())
    return current_week_start + timedelta(weeks=week_offset)


def _fallback_sample_week(start_of_week: date) -> list[dict[str, object]]:
    tz = timezone.get_current_timezone()
    fallback: list[dict[str, object]] = []
    for index, (_, _, events) in enumerate(FALLBACK_WEEK):
        current_date = start_of_week + timedelta(days=index)
        day_label = _weekday_label(datetime.combine(current_date, time.min))
        date_label = current_date.strftime("%d/%m")
        day_events: list[dict[str, object]] = []
        for event_index, event in enumerate(events):
            start, end, service_name, person, *color_override = event
            color = color_override[0] if color_override else _event_colour(event_index)
            start_dt = datetime.combine(current_date, time.fromisoformat(start))
            end_dt = datetime.combine(current_date, time.fromisoformat(end))
            start_iso = timezone.make_aware(start_dt, tz).isoformat()
            end_iso = timezone.make_aware(end_dt, tz).isoformat()
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
        fallback.append({"label": day_label, "date": date_label, "events": day_events})
    return fallback


def _empty_week(start_of_week: date) -> list[dict[str, object]]:
    return [
        {
            "label": _weekday_label(
                datetime.combine(start_of_week + timedelta(days=index), time.min)
            ),
            "date": (start_of_week + timedelta(days=index)).strftime("%d/%m"),
            "events": [],
        }
        for index in range(7)
    ]


def _build_service_lookup(events: list) -> dict[str, Service]:
    """Return a mapping from event titles to Service instances."""

    titles = {event.title for event in events}
    if not titles:
        return {}
    return {
        service.name: service
        for service in Service.objects.filter(name__in=titles).select_related(
            "category"
        )
    }


def _resolve_author(user) -> str:
    """Return the display name for the creator of an event."""

    if user is None:
        return ""
    author_parts = [
        getattr(user, "first_name", "") or "",
        getattr(user, "last_name", "") or "",
    ]
    author = " ".join(part for part in author_parts if part).strip()
    return author or getattr(user, "email", "")


def _event_colour(index: int) -> str:
    return PLANNER_COLOR_PALETTE[index % len(PLANNER_COLOR_PALETTE)]


def _build_event_view(
    event, index: int, service_lookup: dict[str, Service]
) -> EventView:
    """Convert a database event into the EventView structure expected by the UI."""

    start_local = timezone.localtime(event.start_at)
    end_local = timezone.localtime(event.end_at)
    label = _weekday_label(start_local)
    date_label = start_local.strftime("%d/%m")
    service_model = service_lookup.get(event.title)
    service_name = service_model.name if service_model else event.title
    category_name = (
        service_model.category.name if service_model and service_model.category else ""
    )
    author = _resolve_author(event.created_by)
    display_title = f"{author} · {service_name}" if author else service_name

    return EventView(
        label=label,
        date=date_label,
        time=_format_time_range(start_local, end_local),
        title=display_title,
        color=_event_colour(index),
        service=service_name,
        category=category_name,
        description=event.description or "",
        status=event.get_status_display(),
        created_by=author,
        start=start_local.isoformat(),
        end=end_local.isoformat(),
        **_compute_block(start_local, end_local),
    )


def _group_event_views(event_views: list[EventView]) -> list[dict[str, object]]:
    """Group event views by day for easier template consumption."""

    grouped: dict[tuple[str, str], list[EventView]] = defaultdict(list)
    for view in sorted(event_views, key=lambda item: item.start):
        grouped[(view.label, view.date)].append(view)

    ordered_groups = sorted(grouped.items(), key=lambda item: item[1][0].start)
    return [
        {
            "label": label,
            "date": date,
            "events": [view._asdict() for view in views],
        }
        for (label, date), views in ordered_groups
    ]


def build_calendar_events(
    calendar: Calendar | None, week_offset: int = 0
) -> list[dict[str, object]]:
    """Generate planner data either from the database or fallback sample data."""

    start_of_week = _start_of_week(week_offset)

    if calendar is None:
        return _fallback_sample_week(start_of_week)

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start_of_week, time.min), tz)
    end_dt = start_dt + timedelta(days=7)

    queryset = list(
        calendar.events.select_related("created_by")
        .filter(start_at__gte=start_dt, start_at__lt=end_dt)
        .order_by("start_at")
    )
    if not queryset:
        return _empty_week(start_of_week)

    service_lookup = _build_service_lookup(queryset)
    event_views = [
        _build_event_view(event, index, service_lookup)
        for index, event in enumerate(queryset)
    ]
    return _group_event_views(event_views)
