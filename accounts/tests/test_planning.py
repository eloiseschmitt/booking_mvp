"""Tests for planning helpers."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Calendar
from accounts.planning import build_calendar_events

from accounts.planning import _compute_block


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
        )

    def test_empty_calendar_returns_empty_week(self):
        calendar = Calendar.objects.create(
            owner=self.user,
            name="Empty calendar",
            slug="empty-calendar",
        )

        data = build_calendar_events(calendar)

        self.assertTrue(all(not day["events"] for day in data))
        self.assertEqual(len(data), 7)
