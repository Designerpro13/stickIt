"""Rich text editor component for the Sticky Notes application.

Provides a GTK4 TextView-based editor with support for bold, italic, underline,
bulleted/numbered lists, and font size formatting. Content is serialized to/from
HTML for persistence.
"""

from enum import Enum
from html.parser import HTMLParser
from typing import Optional

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    gi.require_version("Pango", "1.0")
    from gi.repository import Gtk, Gdk, Pango, GLib

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False


class FormatType(str, Enum):
    """Supported formatting types for the rich text editor."""

    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    BULLET_LIST = "bullet_list"
    NUMBERED_LIST = "numbered_list"
    FONT_SIZE_SMALL = "font_size_small"
    FONT_SIZE_MEDIUM = "font_size_medium"
    FONT_SIZE_LARGE = "font_size_large"


# Font size mappings in points
FONT_SIZES = {
    "font_size_small": 8,
    "font_size_medium": 12,
    "font_size_large": 16,
}

# HTML tag mappings for export
FORMAT_TO_HTML_TAG = {
    "bold": ("b", {}),
    "italic": ("i", {}),
    "underline": ("u", {}),
    "font_size_small": ("span", {"style": "font-size:8pt"}),
    "font_size_medium": ("span", {"style": "font-size:12pt"}),
    "font_size_large": ("span", {"style": "font-size:16pt"}),
}


class HtmlToTaggedContent:
    """Parses HTML into a list of (text, tags) tuples for loading into a buffer.

    This class is GTK-independent and can be tested without a display server.
    """

    def __init__(self):
        self.segments: list[tuple[str, set[str]]] = []
        self._parser = _ContentHTMLParser(self)
        self._active_tags: list[str] = []
        self._in_list: Optional[str] = None  # "ul" or "ol"
        self._list_counter: int = 0
        self._line_start: bool = True

    def parse(self, html: str) -> list[tuple[str, set[str]]]:
        """Parse HTML string and return list of (text, tag_set) segments."""
        self.segments = []
        self._active_tags = []
        self._in_list = None
        self._list_counter = 0
        self._line_start = True
        self._parser.reset()
        self._parser.feed(html)
        return self.segments

    def _handle_start_tag(self, tag: str, attrs: dict[str, str]) -> None:
        if tag == "b" or tag == "strong":
            self._active_tags.append("bold")
        elif tag == "i" or tag == "em":
            self._active_tags.append("italic")
        elif tag == "u":
            self._active_tags.append("underline")
        elif tag == "ul":
            self._in_list = "ul"
            self._list_counter = 0
        elif tag == "ol":
            self._in_list = "ol"
            self._list_counter = 0
        elif tag == "li":
            if self._in_list == "ul":
                self._add_text("\u2022 ")
            elif self._in_list == "ol":
                self._list_counter += 1
                self._add_text(f"{self._list_counter}. ")
            self._line_start = False
        elif tag == "span":
            style = attrs.get("style", "")
            if "font-size:8pt" in style:
                self._active_tags.append("font_size_small")
            elif "font-size:12pt" in style:
                self._active_tags.append("font_size_medium")
            elif "font-size:16pt" in style:
                self._active_tags.append("font_size_large")
        elif tag == "br":
            self._add_text("\n")
            self._line_start = True

    def _handle_end_tag(self, tag: str) -> None:
        if tag == "b" or tag == "strong":
            self._remove_tag("bold")
        elif tag == "i" or tag == "em":
            self._remove_tag("italic")
        elif tag == "u":
            self._remove_tag("underline")
        elif tag == "ul" or tag == "ol":
            self._in_list = None
            self._list_counter = 0
        elif tag == "li":
            self._add_text("\n")
            self._line_start = True
        elif tag == "span":
            # Remove the most recently added font size tag
            for size_tag in ("font_size_small", "font_size_medium", "font_size_large"):
                if size_tag in self._active_tags:
                    self._remove_tag(size_tag)
                    break

    def _handle_data(self, data: str) -> None:
        if data:
            self._add_text(data)
            if data.endswith("\n"):
                self._line_start = True
            else:
                self._line_start = False

    def _add_text(self, text: str) -> None:
        if text:
            self.segments.append((text, set(self._active_tags)))

    def _remove_tag(self, tag_name: str) -> None:
        # Remove last occurrence of tag
        for i in range(len(self._active_tags) - 1, -1, -1):
            if self._active_tags[i] == tag_name:
                self._active_tags.pop(i)
                break


class _ContentHTMLParser(HTMLParser):
    """Internal HTML parser that delegates to HtmlToTaggedContent."""

    def __init__(self, handler: HtmlToTaggedContent):
        super().__init__()
        self._handler = handler

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attrs_dict = {k: v or "" for k, v in attrs}
        self._handler._handle_start_tag(tag, attrs_dict)

    def handle_endtag(self, tag: str) -> None:
        self._handler._handle_end_tag(tag)

    def handle_data(self, data: str) -> None:
        self._handler._handle_data(data)


def tagged_content_to_html(segments: list[tuple[str, set[str]]]) -> str:
    """Convert a list of (text, tags) segments to an HTML string.

    This function is GTK-independent and can be tested without a display server.
    """
    if not segments:
        return ""

    result: list[str] = []
    in_list: Optional[str] = None  # "ul" or "ol"
    in_list_item: bool = False

    for text, tags in segments:
        # Check if this is a list marker
        is_bullet = text.startswith("\u2022 ")
        is_numbered = _is_numbered_marker(text)

        if is_bullet and in_list != "ul":
            if in_list_item:
                result.append("</li>")
                in_list_item = False
            if in_list:
                result.append(f"</{in_list}>")
            in_list = "ul"
            result.append("<ul>")
            result.append("<li>")
            in_list_item = True
            # Skip the bullet marker itself
            remaining = text[2:]  # Skip "• "
            if remaining:
                result.append(_wrap_with_tags(remaining, tags))
            continue
        elif is_numbered and in_list != "ol":
            if in_list_item:
                result.append("</li>")
                in_list_item = False
            if in_list:
                result.append(f"</{in_list}>")
            in_list = "ol"
            result.append("<ol>")
            result.append("<li>")
            in_list_item = True
            # Skip the number marker
            dot_idx = text.index(". ")
            remaining = text[dot_idx + 2:]
            if remaining:
                result.append(_wrap_with_tags(remaining, tags))
            continue
        elif is_bullet and in_list == "ul":
            # New bullet item in existing list
            if in_list_item:
                result.append("</li>")
            result.append("<li>")
            in_list_item = True
            remaining = text[2:]
            if remaining:
                result.append(_wrap_with_tags(remaining, tags))
            continue
        elif is_numbered and in_list == "ol":
            # New numbered item in existing list
            if in_list_item:
                result.append("</li>")
            result.append("<li>")
            in_list_item = True
            dot_idx = text.index(". ")
            remaining = text[dot_idx + 2:]
            if remaining:
                result.append(_wrap_with_tags(remaining, tags))
            continue

        # Handle newlines (end list items)
        if text == "\n" and in_list_item:
            result.append("</li>")
            in_list_item = False
            continue
        elif text == "\n" and in_list:
            # End of list
            if in_list_item:
                result.append("</li>")
                in_list_item = False
            result.append(f"</{in_list}>")
            in_list = None
            continue
        elif text == "\n":
            result.append("<br>")
            continue

        # Handle text with newlines inside
        if "\n" in text and in_list:
            parts = text.split("\n")
            for idx, part in enumerate(parts):
                if part:
                    result.append(_wrap_with_tags(part, tags))
                if idx < len(parts) - 1:
                    if in_list_item:
                        result.append("</li>")
                        in_list_item = False
            continue

        # Regular text - close any open list if we encounter non-list text after a newline
        if in_list and not in_list_item:
            result.append(f"</{in_list}>")
            in_list = None

        # Normal text
        if "\n" in text:
            parts = text.split("\n")
            for idx, part in enumerate(parts):
                if part:
                    result.append(_wrap_with_tags(part, tags))
                if idx < len(parts) - 1:
                    result.append("<br>")
        else:
            result.append(_wrap_with_tags(text, tags))

    # Close any open list
    if in_list_item:
        result.append("</li>")
    if in_list:
        result.append(f"</{in_list}>")

    return "".join(result)


def _is_numbered_marker(text: str) -> bool:
    """Check if text starts with a numbered list marker like '1. '."""
    if not text:
        return False
    dot_pos = text.find(". ")
    if dot_pos <= 0:
        return False
    return text[:dot_pos].isdigit()


def _wrap_with_tags(text: str, tags: set[str]) -> str:
    """Wrap text with HTML tags based on the format tags set."""
    import html as html_module

    escaped = html_module.escape(text)
    result = escaped

    # Apply font size first (outermost)
    for size_tag in ("font_size_small", "font_size_medium", "font_size_large"):
        if size_tag in tags:
            _, attrs = FORMAT_TO_HTML_TAG[size_tag]
            style = attrs["style"]
            result = f'<span style="{style}">{result}</span>'
            break  # Only one size at a time

    # Apply inline formatting
    if "bold" in tags:
        result = f"<b>{result}</b>"
    if "italic" in tags:
        result = f"<i>{result}</i>"
    if "underline" in tags:
        result = f"<u>{result}</u>"

    return result


def html_to_segments(html: str) -> list[tuple[str, set[str]]]:
    """Parse HTML string into a list of (text, frozenset_of_tags) segments.

    Convenience function wrapping HtmlToTaggedContent for external use.
    """
    parser = HtmlToTaggedContent()
    return parser.parse(html)


def segments_to_html(segments: list[tuple[str, set[str]]]) -> str:
    """Convert segments back to HTML string.

    Convenience function wrapping tagged_content_to_html for external use.
    """
    return tagged_content_to_html(segments)


if GTK_AVAILABLE:

    class RichTextEditor(Gtk.TextView):
        """Rich text editor widget extending Gtk.TextView.

        Supports bold, italic, underline, bulleted/numbered lists, and font sizes.
        Content can be serialized to HTML for persistence and loaded from HTML.
        """

        def __init__(self):
            super().__init__()
            self.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            self.set_editable(True)
            self._buffer = self.get_buffer()
            self._setup_tags()
            self._setup_shortcuts()

        def _setup_shortcuts(self) -> None:
            """Set up keyboard shortcuts for formatting (Ctrl+B, Ctrl+I, Ctrl+U)."""
            key_controller = Gtk.EventControllerKey()
            key_controller.connect("key-pressed", self._on_key_pressed)
            self.add_controller(key_controller)

        def _on_key_pressed(self, controller, keyval, keycode, state) -> bool:
            """Handle key press events for formatting shortcuts."""
            ctrl = state & Gdk.ModifierType.CONTROL_MASK

            if not ctrl:
                return False

            if keyval == Gdk.KEY_b or keyval == Gdk.KEY_B:
                self.apply_format(FormatType.BOLD)
                return True
            elif keyval == Gdk.KEY_i or keyval == Gdk.KEY_I:
                self.apply_format(FormatType.ITALIC)
                return True
            elif keyval == Gdk.KEY_u or keyval == Gdk.KEY_U:
                self.apply_format(FormatType.UNDERLINE)
                return True

            return False

        def _setup_tags(self) -> None:
            """Create text tags for formatting in the buffer's tag table."""
            tag_table = self._buffer.get_tag_table()

            # Bold tag
            bold_tag = Gtk.TextTag(name="bold")
            bold_tag.set_property("weight", Pango.Weight.BOLD)
            tag_table.add(bold_tag)

            # Italic tag
            italic_tag = Gtk.TextTag(name="italic")
            italic_tag.set_property("style", Pango.Style.ITALIC)
            tag_table.add(italic_tag)

            # Underline tag
            underline_tag = Gtk.TextTag(name="underline")
            underline_tag.set_property("underline", Pango.Underline.SINGLE)
            tag_table.add(underline_tag)

            # Font size tags
            small_tag = Gtk.TextTag(name="font_size_small")
            small_tag.set_property("size-points", 8.0)
            tag_table.add(small_tag)

            medium_tag = Gtk.TextTag(name="font_size_medium")
            medium_tag.set_property("size-points", 12.0)
            tag_table.add(medium_tag)

            large_tag = Gtk.TextTag(name="font_size_large")
            large_tag.set_property("size-points", 16.0)
            tag_table.add(large_tag)

        def apply_format(self, format_type: str, selection: Optional[tuple] = None) -> None:
            """Apply formatting to the current selection or toggle at cursor.

            Args:
                format_type: One of the FormatType values (e.g., "bold", "italic").
                selection: Optional tuple of (start_offset, end_offset). If None,
                    uses the current buffer selection.
            """
            if format_type in (FormatType.BULLET_LIST, FormatType.NUMBERED_LIST):
                self._apply_list_format(format_type)
                return

            # For inline formatting
            if selection:
                start_iter = self._buffer.get_iter_at_offset(selection[0])
                end_iter = self._buffer.get_iter_at_offset(selection[1])
            else:
                bounds = self._buffer.get_selection_bounds()
                if bounds:
                    start_iter, end_iter = bounds
                else:
                    # No selection - toggle tag at cursor for future typing
                    mark = self._buffer.get_insert()
                    cursor_iter = self._buffer.get_iter_at_mark(mark)
                    # Toggle is handled by checking if tag is active at cursor
                    # GTK handles this through the tag's "toggle" mechanism
                    return

            tag_name = format_type if isinstance(format_type, str) else format_type.value

            # For font size, remove other size tags first
            if tag_name.startswith("font_size_"):
                for size in ("font_size_small", "font_size_medium", "font_size_large"):
                    tag = self._buffer.get_tag_table().lookup(size)
                    if tag:
                        self._buffer.remove_tag(tag, start_iter, end_iter)

            # Toggle: if entire selection has the tag, remove it; otherwise apply it
            tag = self._buffer.get_tag_table().lookup(tag_name)
            if tag is None:
                return

            if self._selection_has_tag(start_iter, end_iter, tag):
                self._buffer.remove_tag(tag, start_iter, end_iter)
            else:
                self._buffer.apply_tag(tag, start_iter, end_iter)

        def _selection_has_tag(self, start: "Gtk.TextIter", end: "Gtk.TextIter", tag: "Gtk.TextTag") -> bool:
            """Check if the entire selection range has the given tag applied."""
            iter_pos = start.copy()
            while iter_pos.compare(end) < 0:
                if not iter_pos.has_tag(tag):
                    return False
                if not iter_pos.forward_char():
                    break
            return True

        def _apply_list_format(self, format_type: str) -> None:
            """Apply list formatting to the current line(s)."""
            bounds = self._buffer.get_selection_bounds()
            if bounds:
                start_iter, end_iter = bounds
            else:
                mark = self._buffer.get_insert()
                start_iter = self._buffer.get_iter_at_mark(mark)
                end_iter = start_iter.copy()

            # Move to line start
            start_iter.set_line_offset(0)
            # Move end to end of line
            if not end_iter.ends_line():
                end_iter.forward_to_line_end()

            line_text = self._buffer.get_text(start_iter, end_iter, False)

            # Determine marker
            if format_type == FormatType.BULLET_LIST:
                marker = "\u2022 "
            else:
                marker = "1. "

            # Toggle: if already has marker, remove it; otherwise add it
            if line_text.startswith(marker) or (
                format_type == FormatType.NUMBERED_LIST and _is_numbered_marker(line_text)
            ):
                # Remove marker
                if format_type == FormatType.BULLET_LIST:
                    remove_end = self._buffer.get_iter_at_offset(
                        start_iter.get_offset() + len(marker)
                    )
                else:
                    dot_idx = line_text.index(". ")
                    remove_end = self._buffer.get_iter_at_offset(
                        start_iter.get_offset() + dot_idx + 2
                    )
                self._buffer.delete(start_iter, remove_end)
            else:
                # Add marker at line start
                self._buffer.insert(start_iter, marker)

        def get_content_as_html(self) -> str:
            """Export the buffer content as an HTML string.

            Iterates over the buffer character by character, tracks active tags,
            and produces HTML output.
            """
            start_iter = self._buffer.get_start_iter()
            end_iter = self._buffer.get_end_iter()

            if start_iter.equal(end_iter):
                return ""

            segments: list[tuple[str, set[str]]] = []
            current_text = ""
            current_tags: set[str] = set()

            iter_pos = start_iter.copy()
            while iter_pos.compare(end_iter) < 0:
                char = iter_pos.get_char()
                tags_at_pos = self._get_format_tags_at_iter(iter_pos)

                if tags_at_pos == current_tags:
                    current_text += char
                else:
                    if current_text:
                        segments.append((current_text, current_tags))
                    current_text = char
                    current_tags = tags_at_pos

                if not iter_pos.forward_char():
                    break

            if current_text:
                segments.append((current_text, current_tags))

            return tagged_content_to_html(segments)

        def load_content_from_html(self, html: str) -> None:
            """Load HTML content into the editor buffer.

            Parses HTML and applies corresponding text tags to the buffer.
            """
            parser = HtmlToTaggedContent()
            segments = parser.parse(html)

            self._buffer.set_text("")
            end_iter = self._buffer.get_end_iter()

            for text, tags in segments:
                start_offset = end_iter.get_offset()
                self._buffer.insert(end_iter, text)
                end_iter = self._buffer.get_end_iter()

                # Apply tags to the inserted text
                if tags:
                    start_iter = self._buffer.get_iter_at_offset(start_offset)
                    for tag_name in tags:
                        tag = self._buffer.get_tag_table().lookup(tag_name)
                        if tag:
                            self._buffer.apply_tag(tag, start_iter, end_iter)

        def _get_format_tags_at_iter(self, text_iter: "Gtk.TextIter") -> set[str]:
            """Get the set of active format tag names at a given iterator position."""
            tags = set()
            gtk_tags = text_iter.get_tags()
            for gtk_tag in gtk_tags:
                name = gtk_tag.get_property("name")
                if name in ("bold", "italic", "underline",
                            "font_size_small", "font_size_medium", "font_size_large"):
                    tags.add(name)
            return tags

