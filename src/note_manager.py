"""Note manager for coordinating note lifecycle and persistence."""

import logging
from typing import Dict, List

from src.constants import DEFAULT_COLOR, DEFAULT_HEIGHT, DEFAULT_WIDTH
from src.models import Note
from src.persistence import PersistenceStore

logger = logging.getLogger(__name__)


class NoteManager:
    """Central controller managing note lifecycle, coordination between
    views and persistence.

    Attributes:
        _notes: Dictionary mapping note IDs to Note objects.
        _persistence: PersistenceStore instance for save/load operations.
    """

    def __init__(self, persistence_store: PersistenceStore) -> None:
        """Initialize the NoteManager.

        Args:
            persistence_store: The persistence store for saving/loading notes.
        """
        self._notes: Dict[str, Note] = {}
        self._persistence = persistence_store

    def create_note(self, screen_width: int = 1920, screen_height: int = 1080) -> Note:
        """Create a new note with default settings.

        Generates a note with a unique UUID, default dimensions (300x300),
        default color (yellow), and positioned at the center of the screen.

        Args:
            screen_width: The width of the screen in pixels (for centering).
            screen_height: The height of the screen in pixels (for centering).

        Returns:
            The newly created Note object.
        """
        center_x = (screen_width - DEFAULT_WIDTH) // 2
        center_y = (screen_height - DEFAULT_HEIGHT) // 2

        note = Note(
            width=DEFAULT_WIDTH,
            height=DEFAULT_HEIGHT,
            color=DEFAULT_COLOR,
            position_x=center_x,
            position_y=center_y,
        )

        self._notes[note.id] = note
        self._persistence.save_note(note)
        return note

    def delete_note(self, note_id: str) -> None:
        """Remove a note from the active notes and delete its persisted data.

        If the note_id is not found in active notes, logs a warning and
        performs no operation.

        Args:
            note_id: The unique identifier of the note to delete.
        """
        if note_id not in self._notes:
            logger.warning("Attempted to delete non-existent note: %s", note_id)
            return

        del self._notes[note_id]
        self._persistence.delete_note_file(note_id)

    def get_all_notes(self) -> List[Note]:
        """Return all active notes.

        Returns:
            A list of all currently active Note objects.
        """
        return list(self._notes.values())

    def restore_notes(self) -> None:
        """Load all persisted notes and populate the active notes list.

        Calls the persistence store to load all saved notes from disk
        and adds them to the internal tracking dictionary.
        """
        notes = self._persistence.load_all_notes()
        self._notes = {note.id: note for note in notes}

    def reposition_offscreen_note(
        self, note: Note, screen_width: int, screen_height: int
    ) -> None:
        """Clamp a note's position so it remains within the visible screen area.

        Adjusts position_x to be in [0, screen_width - note.width] and
        position_y to be in [0, screen_height - note.height], moving the
        note to the nearest valid position.

        Args:
            note: The Note object to reposition.
            screen_width: The current screen width in pixels.
            screen_height: The current screen height in pixels.
        """
        max_x = max(0, screen_width - note.width)
        max_y = max(0, screen_height - note.height)

        note.position_x = max(0, min(note.position_x, max_x))
        note.position_y = max(0, min(note.position_y, max_y))
