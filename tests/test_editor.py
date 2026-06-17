"""Tests for the RichTextEditor HTML serialization and deserialization logic.

These tests focus on the GTK-independent parts of the editor module:
- HtmlToTaggedContent parser
- tagged_content_to_html export
- Round-trip consistency
"""

import pytest
from src.editor import (
    FormatType,
    HtmlToTaggedContent,
    tagged_content_to_html,
    html_to_segments,
    segments_to_html,
    _wrap_with_tags,
    _is_numbered_marker,
    FONT_SIZES,
)


class TestFormatType:
    """Test the FormatType enum."""

    def test_format_type_values(self):
        assert FormatType.BOLD == "bold"
        assert FormatType.ITALIC == "italic"
        assert FormatType.UNDERLINE == "underline"
        assert FormatType.BULLET_LIST == "bullet_list"
        assert FormatType.NUMBERED_LIST == "numbered_list"
        assert FormatType.FONT_SIZE_SMALL == "font_size_small"
        assert FormatType.FONT_SIZE_MEDIUM == "font_size_medium"
        assert FormatType.FONT_SIZE_LARGE == "font_size_large"


class TestHtmlToTaggedContent:
    """Test HTML parsing into tagged segments."""

    def test_plain_text(self):
        segments = html_to_segments("Hello world")
        assert len(segments) == 1
        assert segments[0] == ("Hello world", set())

    def test_bold_text(self):
        segments = html_to_segments("<b>bold text</b>")
        assert len(segments) == 1
        assert segments[0] == ("bold text", {"bold"})

    def test_italic_text(self):
        segments = html_to_segments("<i>italic text</i>")
        assert len(segments) == 1
        assert segments[0] == ("italic text", {"italic"})

    def test_underline_text(self):
        segments = html_to_segments("<u>underlined</u>")
        assert len(segments) == 1
        assert segments[0] == ("underlined", {"underline"})

    def test_strong_tag_maps_to_bold(self):
        segments = html_to_segments("<strong>bold</strong>")
        assert segments[0] == ("bold", {"bold"})

    def test_em_tag_maps_to_italic(self):
        segments = html_to_segments("<em>italic</em>")
        assert segments[0] == ("italic", {"italic"})

    def test_nested_formatting(self):
        segments = html_to_segments("<b><i>bold italic</i></b>")
        assert len(segments) == 1
        assert segments[0] == ("bold italic", {"bold", "italic"})

    def test_mixed_formatting(self):
        segments = html_to_segments("Hello <b>bold</b> world")
        assert len(segments) == 3
        assert segments[0] == ("Hello ", set())
        assert segments[1] == ("bold", {"bold"})
        assert segments[2] == (" world", set())

    def test_bullet_list(self):
        segments = html_to_segments("<ul><li>item 1</li><li>item 2</li></ul>")
        # Should produce: "• item 1\n• item 2\n"
        texts = "".join(text for text, _ in segments)
        assert "\u2022 item 1" in texts
        assert "\u2022 item 2" in texts

    def test_numbered_list(self):
        segments = html_to_segments("<ol><li>first</li><li>second</li></ol>")
        texts = "".join(text for text, _ in segments)
        assert "1. first" in texts
        assert "2. second" in texts

    def test_font_size_small(self):
        segments = html_to_segments('<span style="font-size:8pt">small</span>')
        assert segments[0] == ("small", {"font_size_small"})

    def test_font_size_medium(self):
        segments = html_to_segments('<span style="font-size:12pt">medium</span>')
        assert segments[0] == ("medium", {"font_size_medium"})

    def test_font_size_large(self):
        segments = html_to_segments('<span style="font-size:16pt">large</span>')
        assert segments[0] == ("large", {"font_size_large"})

    def test_br_tag(self):
        segments = html_to_segments("line1<br>line2")
        texts = "".join(text for text, _ in segments)
        assert "line1" in texts
        assert "\n" in texts
        assert "line2" in texts

    def test_empty_html(self):
        segments = html_to_segments("")
        assert segments == []

    def test_combined_formatting_and_size(self):
        segments = html_to_segments('<b><span style="font-size:16pt">big bold</span></b>')
        assert len(segments) == 1
        assert segments[0] == ("big bold", {"bold", "font_size_large"})


class TestTaggedContentToHtml:
    """Test HTML export from tagged segments."""

    def test_empty_segments(self):
        assert tagged_content_to_html([]) == ""

    def test_plain_text(self):
        segments = [("Hello world", set())]
        assert tagged_content_to_html(segments) == "Hello world"

    def test_bold_text(self):
        segments = [("bold text", {"bold"})]
        assert tagged_content_to_html(segments) == "<b>bold text</b>"

    def test_italic_text(self):
        segments = [("italic text", {"italic"})]
        assert tagged_content_to_html(segments) == "<i>italic text</i>"

    def test_underline_text(self):
        segments = [("underlined", {"underline"})]
        assert tagged_content_to_html(segments) == "<u>underlined</u>"

    def test_combined_bold_italic(self):
        segments = [("both", {"bold", "italic"})]
        html = tagged_content_to_html(segments)
        # Both tags should be present
        assert "<b>" in html
        assert "<i>" in html
        assert "both" in html

    def test_font_size_small(self):
        segments = [("small", {"font_size_small"})]
        html = tagged_content_to_html(segments)
        assert 'font-size:8pt' in html
        assert "small" in html

    def test_font_size_large(self):
        segments = [("large", {"font_size_large"})]
        html = tagged_content_to_html(segments)
        assert 'font-size:16pt' in html

    def test_newline_becomes_br(self):
        segments = [("line1", set()), ("\n", set()), ("line2", set())]
        html = tagged_content_to_html(segments)
        assert "<br>" in html

    def test_bullet_list_export(self):
        segments = [
            ("\u2022 ", set()),
            ("item 1", set()),
            ("\n", set()),
            ("\u2022 ", set()),
            ("item 2", set()),
            ("\n", set()),
        ]
        html = tagged_content_to_html(segments)
        assert "<ul>" in html
        assert "<li>" in html
        assert "item 1" in html
        assert "item 2" in html
        assert "</ul>" in html

    def test_numbered_list_export(self):
        segments = [
            ("1. ", set()),
            ("first", set()),
            ("\n", set()),
            ("2. ", set()),
            ("second", set()),
            ("\n", set()),
        ]
        html = tagged_content_to_html(segments)
        assert "<ol>" in html
        assert "<li>" in html
        assert "first" in html
        assert "second" in html
        assert "</ol>" in html

    def test_html_escaping(self):
        segments = [("x < y & z > w", set())]
        html = tagged_content_to_html(segments)
        assert "&lt;" in html
        assert "&amp;" in html
        assert "&gt;" in html

    def test_mixed_text_and_formatting(self):
        segments = [
            ("Hello ", set()),
            ("world", {"bold"}),
            ("!", set()),
        ]
        html = tagged_content_to_html(segments)
        assert html == "Hello <b>world</b>!"


class TestRoundTrip:
    """Test that HTML -> segments -> HTML produces consistent results."""

    def test_plain_text_round_trip(self):
        original = "Hello world"
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        assert result == original

    def test_bold_round_trip(self):
        original = "<b>bold</b>"
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        assert result == original

    def test_italic_round_trip(self):
        original = "<i>italic</i>"
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        assert result == original

    def test_underline_round_trip(self):
        original = "<u>underline</u>"
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        assert result == original

    def test_mixed_formatting_round_trip(self):
        original = "Hello <b>bold</b> world"
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        assert result == original

    def test_font_size_round_trip(self):
        original = '<span style="font-size:16pt">large</span>'
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        assert result == original

    def test_br_round_trip(self):
        original = "line1<br>line2"
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        assert result == original

    def test_bullet_list_round_trip(self):
        original = "<ul><li>item 1</li><li>item 2</li></ul>"
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        # Verify structural equivalence
        assert "<ul>" in result
        assert "<li>" in result
        assert "item 1" in result
        assert "item 2" in result
        assert "</ul>" in result

    def test_numbered_list_round_trip(self):
        original = "<ol><li>first</li><li>second</li></ol>"
        segments = html_to_segments(original)
        result = segments_to_html(segments)
        assert "<ol>" in result
        assert "<li>" in result
        assert "first" in result
        assert "second" in result
        assert "</ol>" in result


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_is_numbered_marker_valid(self):
        assert _is_numbered_marker("1. text") is True
        assert _is_numbered_marker("12. text") is True
        assert _is_numbered_marker("99. text") is True

    def test_is_numbered_marker_invalid(self):
        assert _is_numbered_marker("") is False
        assert _is_numbered_marker("text") is False
        assert _is_numbered_marker(". text") is False
        assert _is_numbered_marker("a. text") is False

    def test_wrap_with_tags_no_tags(self):
        result = _wrap_with_tags("hello", set())
        assert result == "hello"

    def test_wrap_with_tags_bold(self):
        result = _wrap_with_tags("hello", {"bold"})
        assert result == "<b>hello</b>"

    def test_wrap_with_tags_multiple(self):
        result = _wrap_with_tags("hello", {"bold", "italic"})
        assert "<b>" in result
        assert "<i>" in result
        assert "hello" in result

    def test_wrap_with_tags_escapes_html(self):
        result = _wrap_with_tags("<script>", set())
        assert "&lt;script&gt;" in result

    def test_font_sizes_constants(self):
        assert FONT_SIZES["font_size_small"] == 8
        assert FONT_SIZES["font_size_medium"] == 12
        assert FONT_SIZES["font_size_large"] == 16
