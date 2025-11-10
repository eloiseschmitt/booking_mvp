"""Tests for planning helpers."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import Calendar
from accounts.planning import _compute_block, build_calendar_events


class PlanningHelpersTests(TestCase):
    """Validate layout computations for planning blocks."""

    def test_compute_block_returns_expected_percentages(self):
        """Test that _compute_block returns correct top and height percentages."""
        block = _compute_block("09:00", "10:30")
        self.assertAlmostEqual(block["top_pct"], (60 / (12 * 60)) * 100)
        self.assertAlmostEqual(block["height_pct"], (90 / (12 * 60)) * 100)

    def test_compute_block_minimum_duration(self):
        """Test that _compute_block enforces a minimum height percentage."""
        block = _compute_block("09:00", "09:05")
        self.assertAlmostEqual(block["height_pct"], (30 / (12 * 60)) * 100)


class BuildCalendarEventsTests(TestCase):
    """Tests for build_calendar_events."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="planner@example.com",
            password="safe-password",
            user_type=get_user_model().UserType.PROFESSIONAL,
        )

    def test_empty_calendar_returns_empty_week(self):
        """Ensure build_calendar_events returns seven empty days when no events."""

        calendar = Calendar.objects.create(
            owner=self.user,
            name="Empty calendar",
            slug="empty-calendar",
        )

        data = build_calendar_events(calendar)

        self.assertTrue(all(not day["events"] for day in data))
        self.assertEqual(len(data), 7)

    def test_week_offset_filters_events(self):
        """Events are scoped to the requested week offset."""

        calendar = Calendar.objects.create(
            owner=self.user,
            name="Personal",
            slug="personal",
        )

        base_start = timezone.now().replace(minute=0, second=0, microsecond=0)
        calendar.events.create(
            title="This week",
            start_at=base_start,
            end_at=base_start + timedelta(hours=1),
            status="planned",
        )
        calendar.events.create(
            title="Next week",
            start_at=base_start + timedelta(days=7),
            end_at=base_start + timedelta(days=7, hours=1),
            status="planned",
        )

        this_week = build_calendar_events(calendar, week_offset=0)
        next_week = build_calendar_events(calendar, week_offset=1)

        self.assertEqual(sum(len(day["events"]) for day in this_week), 1)
        self.assertEqual(sum(len(day["events"]) for day in next_week), 1)
