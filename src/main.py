"""Main application entry point for the Sticky Notes application.

Provides the StickyNotesApp class (Gtk.Application subclass) that manages
the application lifecycle, system tray integration, and coordinates between
NoteManager, PersistenceStore, and NoteWindow instances.
"""

import logging
import sys

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import Gtk, Gio, GLib

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from src.autostart import install_autostart, is_autostart_enabled
from src.models import Note
from src.note_manager import NoteManager
from src.persistence import PersistenceStore

logger = logging.getLogger(__name__)

APP_ID = "com.github.stickynotes.app"


class StickyNotesApp(Gtk.Application):
    """GTK4 Application subclass managing the sticky notes app lifecycle.

    Handles note restoration on startup, system tray integration,
    note creation/deletion, and error notifications.
    """

    def __init__(self) -> None:
        """Initialize the application with a unique application ID."""
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._persistence: PersistenceStore | None = None
        self._note_manager: NoteManager | None = None
        self._windows: dict[str, object] = {}

    def do_activate(self) -> None:
        """Called when the application is activated.

        Restores persisted notes, creates NoteWindow for each,
        creates a default note if none exist, sets up system tray,
        and installs autostart on first run.
        """
        self._persistence = PersistenceStore()
        self._note_manager = NoteManager(self._persistence)

        # Restore persisted notes
        self._note_manager.restore_notes()
        notes = self._note_manager.get_all_notes()

        # If no notes exist, create a default one
        if not notes:
            note = self._note_manager.create_note()
            notes = [note]

        # Create a NoteWindow for each restored note
        for note in notes:
            self._spawn_note_window(note)

        # Set up application actions for system tray and shortcuts
        self._setup_actions()

        # Set up system tray indicator (graceful degradation)
        self._setup_system_tray()

        # Install autostart on first run
        if not is_autostart_enabled():
            try:
                install_autostart()
            except OSError as e:
                logger.warning("Failed to install autostart: %s", e)

    def _setup_actions(self) -> None:
        """Register application-level actions for new note and quit."""
        new_note_action = Gio.SimpleAction.new("new-note", None)
        new_note_action.connect("activate", self._on_new_note)
        self.add_action(new_note_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._on_quit)
        self.add_action(quit_action)

    def _setup_system_tray(self) -> None:
        """Set up system tray indicator with New Note and Quit options.

        Uses AyatanaAppIndicator3 if available on the system, otherwise
        degrades gracefully (actions remain accessible via app actions).
        System tray with libappindicator requires GTK3 menus which cannot
        coexist with GTK4 in the same process, so we skip if unavailable.
        """
        try:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3  # noqa: F401

            # AyatanaAppIndicator3 requires GTK3-style menus.
            # Since we run a GTK4 application, we cannot mix GTK3 widgets.
            # Log and degrade gracefully.
            logger.info(
                "AyatanaAppIndicator3 detected but GTK3 menus are incompatible "
                "with GTK4. System tray indicator not activated."
            )
        except (ImportError, ValueError):
            logger.info(
                "System tray indicator not available. "
                "Use app actions (new-note, quit) via desktop integration."
            )

    def _spawn_note_window(self, note: Note) -> None:
        """Create and display a NoteWindow for the given note.

        Args:
            note: The Note model to display in a window.
        """
        from src.note_window import NoteWindow

        window = NoteWindow(
            note=note,
            on_save=self._on_note_save,
            on_delete=self._on_note_delete,
            on_color_change=self._on_note_color_change,
            on_new_note=self._on_create_new_note,
        )
        window.set_application(self)
        self._windows[note.id] = window
        window.present()
        window.focus_editor()

    def _on_create_new_note(self) -> None:
        """Handle new note request from any NoteWindow's + button."""
        if self._note_manager is None:
            return
        note = self._note_manager.create_note()
        self._spawn_note_window(note)

    def _on_new_note(self, action: Gio.SimpleAction, parameter: None) -> None:
        """Handle the 'new-note' action: create a note and spawn its window."""
        if self._note_manager is None:
            return
        note = self._note_manager.create_note()
        self._spawn_note_window(note)

    def _on_quit(self, action: Gio.SimpleAction, parameter: None) -> None:
        """Handle the 'quit' action: close all windows and quit the app."""
        self.quit()

    def _on_note_delete(self, note_id: str) -> None:
        """Handle note deletion request from a NoteWindow.

        Removes the note from the manager and cleans up the window reference.
        """
        if self._note_manager is None:
            return

        self._note_manager.delete_note(note_id)

        # Remove window reference (window closes itself)
        self._windows.pop(note_id, None)

    def _on_note_save(self, note: Note) -> None:
        """Handle save request from a NoteWindow.

        Saves the note through persistence, shows notification on failure.
        """
        if self._persistence is None:
            return

        try:
            self._persistence.save_note(note)
        except OSError as e:
            logger.error("Failed to save note %s: %s", note.id, e)
            self._show_save_error_notification(note)

    def _on_note_color_change(self, note_id: str, color_key: str) -> None:
        """Handle color change from a NoteWindow.

        Triggers a save for the note with the updated color.
        """
        if self._note_manager is None:
            return

        notes = self._note_manager.get_all_notes()
        for note in notes:
            if note.id == note_id:
                self._on_note_save(note)
                break

    def _show_save_error_notification(self, note: Note) -> None:
        """Display a GTK notification when a save operation fails."""
        notification = Gio.Notification.new("Sticky Notes - Save Error")
        notification.set_body(
            "Failed to save note. Please check disk space and permissions."
        )
        notification.set_priority(Gio.NotificationPriority.HIGH)
        self.send_notification("save-error", notification)


def main() -> int:
    """Application entry point.

    Returns:
        Exit code from the application run.
    """
    if not GTK_AVAILABLE:
        print(
            "Error: GTK4 is not available. Please install PyGObject and GTK4.",
            file=sys.stderr,
        )
        return 1

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = StickyNotesApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
