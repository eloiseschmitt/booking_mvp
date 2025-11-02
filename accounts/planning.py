"""Static planning helpers and dynamic data retrieval for the dashboard."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import NamedTuple, Sequence

from django.utils import timezone

from .constants import PLANNER_COLOR_PALETTE, PLANNER_HOURS, TOTAL_PLANNER_SPAN_MINUTES
from .models import Calendar, Event


class _EventView(NamedTuple):
    label: str
    date: str
    time: str
    title: str
    color: str
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


def _fallback_sample_week() -> list[dict[str, object]]:
    return [
        {
            "label": "Lun.",
            "date": "15/09",
            "events": [
                {
                    "time": "09:00 – 10:05",
                    "title": "Camille Thomas · Modelage bien-être",
                    "color": "#7C8FF8",
                    **_compute_block("09:00", "10:05"),
                },
                {
                    "time": "11:30 – 12:30",
                    "title": "Valérie · Soin découverte",
                    "color": "#E07B39",
                    **_compute_block("11:30", "12:30"),
                },
                {
                    "time": "14:00 – 15:20",
                    "title": "Valérie · Soin corps complet",
                    "color": "#6BC0A5",
                    **_compute_block("14:00", "15:20"),
                },
                {
                    "time": "17:00 – 17:55",
                    "title": "Jackie Vernhères · Modelage",
                    "color": "#AF77E5",
                    **_compute_block("17:00", "17:55"),
                },
            ],
        },
        {
            "label": "Mar.",
            "date": "16/09",
            "events": [
                {
                    "time": "09:40 – 10:35",
                    "title": "Laetitia · Kobido visage",
                    "color": "#2CB7C6",
                    **_compute_block("09:40", "10:35"),
                },
                {
                    "time": "12:30 – 13:30",
                    "title": "Valérie · Entreprise",
                    "color": "#A7B0C0",
                    **_compute_block("12:30", "13:30"),
                },
                {
                    "time": "14:00 – 14:45",
                    "title": "Prate Michelle · Massage",
                    "color": "#F06FA7",
                    **_compute_block("14:00", "14:45"),
                },
            ],
        },
        {
            "label": "Mer.",
            "date": "17/09",
            "events": [
                {
                    "time": "09:00 – 14:00",
                    "title": "Bloc formation interne",
                    "color": "#D1D7E0",
                    **_compute_block("09:00", "14:00"),
                }
            ],
        },
        {
            "label": "Jeu.",
            "date": "18/09",
            "events": [
                {
                    "time": "09:15 – 09:45",
                    "title": "Manon · Mise en beauté",
                    "color": "#4AC07A",
                    **_compute_block("09:15", "09:45"),
                },
                {
                    "time": "11:15 – 12:15",
                    "title": "Danny · Soin éclat intense",
                    "color": "#5272FF",
                    **_compute_block("11:15", "12:15"),
                },
                {
                    "time": "14:15 – 15:20",
                    "title": "Sarah B. · Modelage",
                    "color": "#AF77E5",
                    **_compute_block("14:15", "15:20"),
                },
                {
                    "time": "17:00 – 17:45",
                    "title": "Isabelle · Rehaussement de cils",
                    "color": "#FFB347",
                    **_compute_block("17:00", "17:45"),
                },
            ],
        },
        {
            "label": "Ven.",
            "date": "19/09",
            "events": [
                {
                    "time": "09:00 – 09:35",
                    "title": "Séverine · Pose vernis",
                    "color": "#4AC07A",
                    **_compute_block("09:00", "09:35"),
                },
                {
                    "time": "11:00 – 12:00",
                    "title": "Sabrina · Forfait duo",
                    "color": "#E07B39",
                    **_compute_block("11:00", "12:00"),
                },
                {
                    "time": "18:00 – 18:25",
                    "title": "Cousine Laure · Conseils",
                    "color": "#F06FA7",
                    **_compute_block("18:00", "18:25"),
                },
            ],
        },
        {
            "label": "Sam.",
            "date": "20/09",
            "events": [
                {
                    "time": "09:00 – 10:30",
                    "title": "Coaching maquillage",
                    "color": "#7C8FF8",
                    **_compute_block("09:00", "10:30"),
                },
                {
                    "time": "14:00 – 15:30",
                    "title": "Atelier collectif",
                    "color": "#6BC0A5",
                    **_compute_block("14:00", "15:30"),
                },
            ],
        },
        {
            "label": "Dim.",
            "date": "21/09",
            "events": [],
        },
    ]


def build_calendar_events(calendar: Calendar | None) -> list[dict[str, object]]:
    """Generate planner data either from the database or fallback sample data."""

    if calendar is None:
        return _fallback_sample_week()

    events_by_day: dict[tuple[str, str], list[_EventView]] = defaultdict(list)
    queryset = calendar.events.select_related("created_by").order_by("start_at")
    for index, event in enumerate(queryset):
        start_local = timezone.localtime(event.start_at)
        end_local = timezone.localtime(event.end_at)
        label = _weekday_label(start_local)
        date_label = start_local.strftime("%d/%m")
        color = PLANNER_COLOR_PALETTE[index % len(PLANNER_COLOR_PALETTE)]
        display_title = event.title
        if event.created_by:
            author_parts = [getattr(event.created_by, "first_name", ""), getattr(event.created_by, "last_name", "")]
            author = " ".join(part for part in author_parts if part).strip() or getattr(event.created_by, "email", "")
            display_title = f"{author} · {event.title}"

        events_by_day[label, date_label].append(
            _EventView(
                label=label,
                date=date_label,
                time=_format_time_range(start_local, end_local),
                title=display_title,
                color=color,
                **_compute_block(start_local, end_local),
            )
        )

    if not events_by_day:
        return _fallback_sample_week()

    grouped: list[dict[str, object]] = []
    for (label, date_label), events in sorted(events_by_day.items(), key=lambda item: datetime.strptime(item[0][1], "%d/%m")):
        grouped.append(
            {
                "label": label,
                "date": date_label,
                "events": [event._asdict() for event in events],
            }
        )

    return grouped


SAMPLE_WEEK = _fallback_sample_week()
