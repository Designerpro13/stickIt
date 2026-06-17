"""Unit tests for resize constraint logic."""

import pytest

from src.constants import MIN_HEIGHT, MIN_WIDTH
from src.note_window import apply_resize_constraints


class TestApplyResizeConstraints:
    """Tests for apply_resize_constraints function."""

    def test_values_within_bounds_unchanged(self):
        """Values within [MIN, screen] should pass through unchanged."""
        width, height = 400, 300
        screen_w, screen_h = 1920, 1080
        result = apply_resize_constraints(width, height, screen_w, screen_h)
        assert result == (400, 300)

    def test_width_below_minimum_clamped_up(self):
        """Width below MIN_WIDTH is clamped up to MIN_WIDTH."""
        result = apply_resize_constraints(50, 300, 1920, 1080)
        assert result[0] == MIN_WIDTH

    def test_height_below_minimum_clamped_up(self):
        """Height below MIN_HEIGHT is clamped up to MIN_HEIGHT."""
        result = apply_resize_constraints(300, 50, 1920, 1080)
        assert result[1] == MIN_HEIGHT

    def test_width_above_screen_clamped_down(self):
        """Width above screen_width is clamped down to screen_width."""
        result = apply_resize_constraints(5000, 300, 1920, 1080)
        assert result[0] == 1920

    def test_height_above_screen_clamped_down(self):
        """Height above screen_height is clamped down to screen_height."""
        result = apply_resize_constraints(300, 5000, 1920, 1080)
        assert result[1] == 1080

    def test_both_below_minimum(self):
        """Both dimensions below minimum are clamped up."""
        result = apply_resize_constraints(10, 10, 1920, 1080)
        assert result == (MIN_WIDTH, MIN_HEIGHT)

    def test_both_above_screen(self):
        """Both dimensions above screen are clamped down."""
        result = apply_resize_constraints(5000, 5000, 1920, 1080)
        assert result == (1920, 1080)

    def test_width_exactly_at_minimum(self):
        """Width exactly at MIN_WIDTH remains unchanged."""
        result = apply_resize_constraints(MIN_WIDTH, 300, 1920, 1080)
        assert result[0] == MIN_WIDTH

    def test_height_exactly_at_minimum(self):
        """Height exactly at MIN_HEIGHT remains unchanged."""
        result = apply_resize_constraints(300, MIN_HEIGHT, 1920, 1080)
        assert result[1] == MIN_HEIGHT

    def test_width_exactly_at_screen_width(self):
        """Width exactly at screen_width remains unchanged."""
        result = apply_resize_constraints(1920, 300, 1920, 1080)
        assert result[0] == 1920

    def test_height_exactly_at_screen_height(self):
        """Height exactly at screen_height remains unchanged."""
        result = apply_resize_constraints(300, 1080, 1920, 1080)
        assert result[1] == 1080

    def test_zero_dimensions(self):
        """Zero dimensions are clamped to minimums."""
        result = apply_resize_constraints(0, 0, 1920, 1080)
        assert result == (MIN_WIDTH, MIN_HEIGHT)

    def test_negative_dimensions(self):
        """Negative dimensions are clamped to minimums."""
        result = apply_resize_constraints(-100, -50, 1920, 1080)
        assert result == (MIN_WIDTH, MIN_HEIGHT)
