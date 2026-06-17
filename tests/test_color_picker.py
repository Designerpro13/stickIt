"""Unit tests for the color picker module (non-GTK logic)."""

import pytest

from src.color_picker import _create_color_css, create_note_background_css
from src.constants import COLOR_PALETTE


class TestCreateColorCss:
    """Tests for _create_color_css helper function."""

    def test_generates_css_with_correct_background_color(self):
        """Generated CSS sets the correct background-color property."""
        css = _create_color_css("yellow", "#FFEB3B")
        assert "background-color: #FFEB3B" in css

    def test_generates_css_with_correct_class_name(self):
        """Generated CSS uses the color key in the class name."""
        css = _create_color_css("blue", "#BBDEFB")
        assert ".color-btn-blue" in css

    def test_generates_hover_state(self):
        """Generated CSS includes a hover state."""
        css = _create_color_css("green", "#C8E6C9")
        assert ".color-btn-green:hover" in css

    def test_all_palette_colors_produce_valid_css(self):
        """All colors in COLOR_PALETTE produce non-empty CSS."""
        for color_key, hex_color in COLOR_PALETTE.items():
            css = _create_color_css(color_key, hex_color)
            assert len(css) > 0
            assert f".color-btn-{color_key}" in css
            assert f"background-color: {hex_color}" in css


class TestCreateNoteBackgroundCss:
    """Tests for create_note_background_css function."""

    def test_generates_css_with_note_window_class(self):
        """Generated CSS targets the note-window class."""
        css = create_note_background_css("#FFEB3B")
        assert "window.note-window" in css

    def test_generates_css_with_correct_color(self):
        """Generated CSS sets the correct background-color."""
        css = create_note_background_css("#BBDEFB")
        assert "background-color: #BBDEFB" in css

    def test_styles_textview_for_consistent_background(self):
        """Generated CSS also styles the textview to match the window background."""
        css = create_note_background_css("#F8BBD0")
        assert "textview" in css
        # The textview text element should also be styled
        assert "textview text" in css

    def test_all_palette_colors_produce_valid_background_css(self):
        """All colors in COLOR_PALETTE produce valid background CSS."""
        for color_key, hex_color in COLOR_PALETTE.items():
            css = create_note_background_css(hex_color)
            assert "note-window" in css
            assert hex_color in css
