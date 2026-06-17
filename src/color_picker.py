"""Color palette popover component for the Sticky Notes application.

Provides a ColorPalettePopover class that displays a grid of colored buttons.
When a color is selected, it triggers a callback with the color key and hex value.
"""

from typing import Callable, Optional

from src.constants import COLOR_PALETTE

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Gtk, Gdk

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False


def _create_color_css(color_key: str, hex_color: str) -> str:
    """Generate CSS for a color button.

    Args:
        color_key: The color name key (e.g., 'yellow').
        hex_color: The hex color value (e.g., '#FFEB3B').

    Returns:
        A CSS string that styles the button with the given background color.
    """
    return (
        f".color-btn-{color_key} {{\n"
        f"  background-color: {hex_color};\n"
        f"  border-radius: 50%;\n"
        f"  min-width: 24px;\n"
        f"  min-height: 24px;\n"
        f"  padding: 0;\n"
        f"  margin: 2px;\n"
        f"  border: 1px solid rgba(0, 0, 0, 0.2);\n"
        f"}}\n"
        f".color-btn-{color_key}:hover {{\n"
        f"  border: 2px solid rgba(0, 0, 0, 0.5);\n"
        f"}}\n"
    )


def create_note_background_css(hex_color: str) -> str:
    """Generate CSS for a note window background color.

    Args:
        hex_color: The hex color value to apply as the window background.

    Returns:
        A CSS string that sets the window background to the specified color.
    """
    return (
        f"window.note-window {{\n"
        f"  background-color: {hex_color};\n"
        f"}}\n"
        f"window.note-window .content-area {{\n"
        f"  background-color: {hex_color};\n"
        f"}}\n"
        f"window.note-window textview {{\n"
        f"  background-color: {hex_color};\n"
        f"}}\n"
        f"window.note-window textview text {{\n"
        f"  background-color: {hex_color};\n"
        f"}}\n"
    )


if GTK_AVAILABLE:

    class ColorPalettePopover(Gtk.Popover):
        """A popover containing a grid of color buttons for note color selection.

        The popover displays the predefined colors from COLOR_PALETTE in a grid
        layout. When a color is clicked, it calls the on_color_selected callback
        with the color key.

        This class can be attached to any Gtk.Widget using set_parent().

        Usage:
            def handle_color(color_key: str):
                print(f"Selected: {color_key}")

            popover = ColorPalettePopover(on_color_selected=handle_color)
            popover.set_parent(some_button)
            popover.popup()
        """

        def __init__(self, on_color_selected: Optional[Callable[[str], None]] = None):
            """Initialize the color palette popover.

            Args:
                on_color_selected: Callback invoked with the color key string
                    when a color button is clicked. If None, selections are ignored.
            """
            super().__init__()
            self._on_color_selected = on_color_selected
            self._css_provider = Gtk.CssProvider()
            self._setup_ui()

        def _setup_ui(self) -> None:
            """Build the grid of color buttons inside the popover."""
            grid = Gtk.Grid()
            grid.set_row_spacing(4)
            grid.set_column_spacing(4)
            grid.set_margin_top(8)
            grid.set_margin_bottom(8)
            grid.set_margin_start(8)
            grid.set_margin_end(8)

            # Generate CSS for all color buttons
            css_text = ""
            for color_key, hex_color in COLOR_PALETTE.items():
                css_text += _create_color_css(color_key, hex_color)

            self._css_provider.load_from_data(css_text.encode())

            # Arrange colors in a grid: 4 columns
            columns = 4
            for idx, (color_key, hex_color) in enumerate(COLOR_PALETTE.items()):
                row = idx // columns
                col = idx % columns

                button = Gtk.Button()
                button.set_size_request(28, 28)
                button.add_css_class(f"color-btn-{color_key}")
                button.set_tooltip_text(color_key.capitalize())

                # Apply CSS to this button's display
                button.get_style_context().add_provider(
                    self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )

                # Connect click handler with the color key
                button.connect("clicked", self._on_button_clicked, color_key)

                grid.attach(button, col, row, 1, 1)

            self.set_child(grid)

        def _on_button_clicked(self, button: "Gtk.Button", color_key: str) -> None:
            """Handle a color button click.

            Args:
                button: The clicked button widget.
                color_key: The color key associated with the button.
            """
            self.popdown()
            if self._on_color_selected:
                self._on_color_selected(color_key)

        def set_on_color_selected(self, callback: Callable[[str], None]) -> None:
            """Set or update the color selection callback.

            Args:
                callback: Function to call with the color key when a color is selected.
            """
            self._on_color_selected = callback


def apply_note_background_color(
    window: "Gtk.Window",
    css_provider: "Gtk.CssProvider",
    color_key: str,
) -> None:
    """Apply a background color to a note window using CSS.

    Updates the CSS provider with the appropriate background color and
    ensures it's attached to the window's style context.

    Args:
        window: The GTK window to style.
        css_provider: A CssProvider instance to load the new CSS into.
        color_key: A key from COLOR_PALETTE (e.g., 'yellow', 'blue').
    """
    if not GTK_AVAILABLE:
        return

    hex_color = COLOR_PALETTE.get(color_key)
    if hex_color is None:
        return

    css_text = create_note_background_css(hex_color)
    css_provider.load_from_data(css_text.encode())

    # Ensure the provider is added to the window's style context
    style_context = window.get_style_context()
    style_context.add_provider(
        css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
