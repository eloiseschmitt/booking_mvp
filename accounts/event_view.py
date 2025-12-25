"""Typed tuple representation for planner events."""

from __future__ import annotations

from typing import NamedTuple


class EventView(NamedTuple):
    """Structured data returned to the planner template for each event."""

    event_id: int
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
    client: str
    start: str
    end: str
    top_pct: float
    height_pct: float
