"""Note window module for the Sticky Notes application.

Provides the NoteWindow GTK4 widget representing a single sticky note on the
desktop with custom title bar, rich text editor, drag-to-move, resize support,
and debounced autosave.
"""

from typing import Callable, Optional

from src.constants import (
    MIN_WIDTH,
    MIN_HEIGHT,
    AUTOSAVE_DELAY_MS,
    COLOR_PALETTE,
    DEFAULT_COLOR,
)
from src.models import Note

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Gtk, Gdk, GLib

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False


def apply_resize_constraints(
    width: int, height: int, screen_width: int, screen_height: int
) -> tuple[int, int]:
    """Clamp note dimensions to valid bounds.

    Width is clamped to [MIN_WIDTH, screen_width].
    Height is clamped to [MIN_HEIGHT, screen_height].

    Args:
        width: Requested width in pixels.
        height: Requested height in pixels.
        screen_width: Maximum allowed width (screen width).
        screen_height: Maximum allowed height (screen height).

    Returns:
        A tuple (clamped_width, clamped_height).
    """
    clamped_width = max(MIN_WIDTH, min(width, screen_width))
    clamped_height = max(MIN_HEIGHT, min(height, screen_height))
    return (clamped_width, clamped_height)


if GTK_AVAILABLE:
    from src.editor import RichTextEditor
    from src.color_picker import (
        ColorPalettePopover,
        apply_note_background_color,
    )

    class NoteWindow(Gtk.Window):
        """GTK4 window representing a single sticky note on the desktop.

        Features:
        - Desktop widget behavior (below other windows by default)
        - Custom title bar with close button, color picker, and pin toggle
        - Embedded RichTextEditor as main content area
        - Drag-to-move via title bar
        - Resize via window edges/corners with dimension constraints
        - Debounced autosave on content changes (2-second delay)

        Args:
            note: The Note data model to display.
            on_save: Callback invoked with the Note when content should be saved.
            on_delete: Callback invoked with the note ID when the note is deleted.
            on_color_change: Callback invoked with (note_id, color_key) on color change.
        """

        def __init__(
            self,
            note: Note,
            on_save: Optional[Callable[[Note], None]] = None,
            on_delete: Optional[Callable[[str], None]] = None,
            on_color_change: Optional[Callable[[str, str], None]] = None,
        ):
            super().__init__()
            self._note = note
            self._on_save = on_save
            self._on_delete = on_delete
            self._on_color_change = on_color_change
            self._autosave_timeout_id: Optional[int] = None
            self._is_pinned: bool = note.always_on_top
            self._bg_css_provider = Gtk.CssProvider()

            self._setup_window()
            self._build_ui()
            self._apply_initial_color()
            self._connect_signals()
            self._load_content()

        @property
        def note(self) -> Note:
            """Get the note model associated with this window."""
            return self._note

        # --- Window setup ---

        def _setup_window(self) -> None:
            """Configure the window properties for desktop widget behavior."""
            self.add_css_class("note-window")
            self.set_title("Sticky Note")
            self.set_default_size(self._note.width, self._note.height)
            self.set_resizable(True)

            # Remove default system decorations for a fully custom title bar
            self.set_decorated(False)

            # If note is pinned, apply always-on-top
            if self._is_pinned:
                self._apply_always_on_top(True)

            # Best-effort positioning (X11 only; Wayland doesn't support programmatic positioning)
            self.connect("realize", self._on_realize)

        def _on_realize(self, widget: "Gtk.Widget") -> None:
            """Handle window realization for X11-specific positioning."""
            surface = self.get_surface()
            if surface is None:
                return
            # On X11, we can try to position the window at saved coordinates.
            # GTK4 on Wayland ignores positioning, so this is best-effort.
            try:
                display = self.get_display()
                display_name = display.get_name() if display else ""
                if display_name and "x11" in display_name.lower():
                    # X11: use the GdkX11Surface if available
                    if hasattr(surface, "move"):
                        surface.move(self._note.position_x, self._note.position_y)
            except Exception:
                pass

        # --- UI construction ---

        def _build_ui(self) -> None:
            """Build the note window UI layout: title bar + editor."""
            # Main vertical box
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.set_child(main_box)

            # Custom title bar
            self._title_bar = self._build_title_bar()
            main_box.append(self._title_bar)

            # Rich text editor as main content area
            self._editor = RichTextEditor()
            self._editor.set_vexpand(True)
            self._editor.set_hexpand(True)
            self._editor.set_left_margin(12)
            self._editor.set_right_margin(12)
            self._editor.set_top_margin(8)
            self._editor.set_bottom_margin(8)

            # Wrap editor in a scrolled window for long content
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_child(self._editor)
            scrolled.set_vexpand(True)
            scrolled.set_hexpand(True)
            scrolled.add_css_class("content-area")
            main_box.append(scrolled)

        def _build_title_bar(self) -> Gtk.Box:
            """Build the custom title bar with pin, color picker, and close buttons."""
            title_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            title_bar.add_css_class("title-bar")
            title_bar.set_margin_start(4)
            title_bar.set_margin_end(4)
            title_bar.set_margin_top(4)
            title_bar.set_margin_bottom(2)

            # Pin (always-on-top) toggle button
            self._pin_button = Gtk.Button(label="\U0001f4cc")  # 📌
            self._pin_button.set_tooltip_text("Toggle always on top")
            self._pin_button.add_css_class("flat")
            if self._is_pinned:
                self._pin_button.add_css_class("pinned")
            self._pin_button.connect("clicked", self._on_pin_toggled)
            title_bar.append(self._pin_button)

            # Color picker button
            color_button = Gtk.Button(label="\U0001f3a8")  # 🎨
            color_button.set_tooltip_text("Change note color")
            color_button.add_css_class("flat")
            self._color_popover = ColorPalettePopover(
                on_color_selected=self._handle_color_selected
            )
            self._color_popover.set_parent(color_button)
            color_button.connect("clicked", self._on_color_button_clicked)
            title_bar.append(color_button)

            # Spacer to push close button to the right (also serves as drag handle)
            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            title_bar.append(spacer)

            # Close (delete) button
            close_button = Gtk.Button(label="\u2715")  # ✕
            close_button.set_tooltip_text("Delete note")
            close_button.add_css_class("flat")
            close_button.connect("clicked", self._on_close_clicked)
            title_bar.append(close_button)

            # Drag gesture on the spacer only, so buttons remain clickable
            drag_gesture = Gtk.GestureDrag()
            drag_gesture.connect("drag-begin", self._on_drag_begin)
            drag_gesture.connect("drag-update", self._on_drag_update)
            drag_gesture.connect("drag-end", self._on_drag_end)
            spacer.add_controller(drag_gesture)

            return title_bar

        # --- Signal connections ---

        def _connect_signals(self) -> None:
            """Connect editor buffer changes and resize signals."""
            # Autosave on content change
            buffer = self._editor.get_buffer()
            buffer.connect("changed", self._on_content_changed)

            # Track resize via the notify signal on default-width/default-height
            self.connect("notify::default-width", self._on_resize)
            self.connect("notify::default-height", self._on_resize)

        def _load_content(self) -> None:
            """Load note content into the editor."""
            if self._note.content:
                self._editor.load_content_from_html(self._note.content)

        # --- Title bar action handlers ---

        def _on_pin_toggled(self, button: "Gtk.Button") -> None:
            """Toggle always-on-top state."""
            self._is_pinned = not self._is_pinned
            self._note.always_on_top = self._is_pinned
            self._apply_always_on_top(self._is_pinned)

            if self._is_pinned:
                button.add_css_class("pinned")
            else:
                button.remove_css_class("pinned")

            self._schedule_autosave()

        def _apply_always_on_top(self, on_top: bool) -> None:
            """Apply always-on-top or desktop-level window stacking.

            In GTK4, full always-on-top depends on compositor support.
            We use present() as a best-effort approach.
            """
            if on_top:
                self.present()

        def _on_color_button_clicked(self, button: "Gtk.Button") -> None:
            """Show the color palette popover."""
            self._color_popover.popup()

        def _handle_color_selected(self, color_key: str) -> None:
            """Handle color selection from the palette popover."""
            self.set_background_color(color_key)
            self._note.color = color_key
            if self._on_color_change:
                self._on_color_change(self._note.id, color_key)
            self._schedule_autosave()

        def _on_close_clicked(self, button: "Gtk.Button") -> None:
            """Handle close/delete button click."""
            # Cancel any pending autosave
            if self._autosave_timeout_id is not None:
                GLib.source_remove(self._autosave_timeout_id)
                self._autosave_timeout_id = None

            if self._on_delete:
                self._on_delete(self._note.id)

            self.close()

        # --- Drag-to-move ---

        def _on_drag_begin(
            self, gesture: "Gtk.GestureDrag", start_x: float, start_y: float
        ) -> None:
            """Initiate window move via the windowing system's interactive move."""
            surface = self.get_surface()
            if surface is None:
                return

            # GdkToplevel (GTK4) supports begin_move for interactive window movement
            toplevel = surface
            if hasattr(toplevel, "begin_move"):
                device = gesture.get_device()
                button = gesture.get_current_button()
                timestamp = Gdk.CURRENT_TIME
                # Translate local coords to root coords for the move request
                native = self.get_native()
                if native:
                    root_x, root_y = start_x, start_y
                    # Attempt to get surface-relative offset
                    try:
                        sx, sy = native.get_surface_transform()
                        root_x += sx
                        root_y += sy
                    except Exception:
                        pass
                    toplevel.begin_move(
                        device, int(button), root_x, root_y, timestamp
                    )

        def _on_drag_update(
            self, gesture: "Gtk.GestureDrag", offset_x: float, offset_y: float
        ) -> None:
            """Handle drag updates (actual movement handled by the windowing system)."""
            pass

        def _on_drag_end(
            self, gesture: "Gtk.GestureDrag", offset_x: float, offset_y: float
        ) -> None:
            """Save position after drag ends."""
            # Update note model position (best-effort via surface position)
            surface = self.get_surface()
            if surface is not None and hasattr(surface, "get_position"):
                try:
                    x, y = surface.get_position()
                    self._note.position_x = int(x)
                    self._note.position_y = int(y)
                except Exception:
                    pass
            self._schedule_autosave()

        # --- Resize handling ---

        def _on_resize(self, widget: "Gtk.Window", param) -> None:
            """Handle window resize events and apply constraints."""
            width = self.get_width()
            height = self.get_height()

            # Get screen dimensions for constraint clamping
            display = self.get_display()
            if display is not None:
                monitors = display.get_monitors()
                if monitors.get_n_items() > 0:
                    monitor = monitors.get_item(0)
                    geometry = monitor.get_geometry()
                    screen_width = geometry.width
                    screen_height = geometry.height

                    clamped_w, clamped_h = apply_resize_constraints(
                        width, height, screen_width, screen_height
                    )

                    self._note.width = clamped_w
                    self._note.height = clamped_h

                    # Enforce constraints if dimensions were clamped
                    if clamped_w != width or clamped_h != height:
                        self.set_default_size(clamped_w, clamped_h)
                else:
                    self._note.width = width
                    self._note.height = height
            else:
                self._note.width = width
                self._note.height = height

            self._schedule_autosave()

        # --- Autosave (debounced) ---

        def _on_content_changed(self, buffer) -> None:
            """Handle text buffer content change with debounced autosave."""
            self._schedule_autosave()

        def _schedule_autosave(self) -> None:
            """Schedule a debounced autosave. Cancels any existing pending save."""
            if self._autosave_timeout_id is not None:
                GLib.source_remove(self._autosave_timeout_id)

            self._autosave_timeout_id = GLib.timeout_add(
                AUTOSAVE_DELAY_MS, self._perform_autosave
            )

        def _perform_autosave(self) -> bool:
            """Execute the autosave: update note content and invoke on_save callback.

            Returns False to prevent GLib from repeating the timeout.
            """
            self._autosave_timeout_id = None

            # Update note content from editor
            self._note.content = self._editor.get_content_as_html()

            # Update modified timestamp
            from datetime import datetime, timezone

            self._note.modified_at = datetime.now(timezone.utc).isoformat()

            if self._on_save:
                self._on_save(self._note)

            return False  # Don't repeat the timeout

        # --- Color ---

        def _apply_initial_color(self) -> None:
            """Apply the note's current color on window creation."""
            color = self._note.color if self._note.color in COLOR_PALETTE else DEFAULT_COLOR
            self.set_background_color(color)

        # --- Public API ---

        def set_background_color(self, color_key: str) -> None:
            """Update the note window background color.

            Args:
                color_key: A key from COLOR_PALETTE (e.g., 'yellow', 'blue').
            """
            apply_note_background_color(self, self._bg_css_provider, color_key)

        def set_sticky_mode(self, always_on_top: bool) -> None:
            """Toggle between desktop-level and always-on-top.

            Args:
                always_on_top: If True, note stays above all windows.
                    If False, note stays below normal windows (desktop widget).
            """
            self._is_pinned = always_on_top
            self._note.always_on_top = always_on_top
            self._apply_always_on_top(always_on_top)

            if always_on_top:
                self._pin_button.add_css_class("pinned")
            else:
                self._pin_button.remove_css_class("pinned")

        def focus_editor(self) -> None:
            """Place keyboard focus in the editor for immediate typing."""
            self._editor.grab_focus()
