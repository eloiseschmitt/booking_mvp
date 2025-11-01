"""Tests for planning helpers."""

from django.test import TestCase

from accounts.planning import _compute_block


class PlanningHelpersTests(TestCase):
    """Validate layout computations for planning blocks."""

    def test_compute_block_returns_expected_percentages(self):
        block = _compute_block("09:00", "10:30")
        self.assertAlmostEqual(block["top_pct"], (60 / (12 * 60)) * 100)
        self.assertAlmostEqual(block["height_pct"], (90 / (12 * 60)) * 100)

    def test_compute_block_minimum_duration(self):
        block = _compute_block("09:00", "09:05")
        self.assertAlmostEqual(block["height_pct"], (30 / (12 * 60)) * 100)
