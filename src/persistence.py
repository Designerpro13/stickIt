"""Persistence store for saving and loading sticky notes as JSON files."""

import json
import logging
import os
from dataclasses import asdict
from typing import List, Optional

from src.constants import STORAGE_DIR
from src.models import Note

logger = logging.getLogger(__name__)


class PersistenceStore:
    """Handles JSON serialization/deserialization of notes to disk.

    Notes are stored as individual JSON files in the XDG data directory
    at ~/.local/share/sticky-notes-app/notes/{id}.json.
    """

    def __init__(self, storage_dir: str = STORAGE_DIR):
        """Initialize the persistence store.

        Args:
            storage_dir: Directory path where note JSON files are stored.
                         Defaults to the XDG data directory.
        """
        self._storage_dir = storage_dir

    def _ensure_storage_dir(self) -> None:
        """Create the storage directory if it does not exist."""
        os.makedirs(self._storage_dir, exist_ok=True)

    def serialize(self, note: Note) -> str:
        """Convert a Note object to a pretty-printed JSON string.

        Args:
            note: The Note object to serialize.

        Returns:
            A pretty-printed JSON string (indent=2) representing the note.
        """
        return json.dumps(asdict(note), indent=2)

    def deserialize(self, json_str: str) -> Note:
        """Parse a JSON string into a Note object.

        Args:
            json_str: A JSON string representing a note.

        Returns:
            A Note object populated from the JSON data.

        Raises:
            json.JSONDecodeError: If the string is not valid JSON.
            TypeError: If the JSON data doesn't match Note fields.
        """
        data = json.loads(json_str)
        return Note(**data)

    def save_note(self, note: Note) -> None:
        """Serialize and write a note to its JSON file.

        Creates the storage directory if it doesn't exist, then writes
        the note as pretty-printed JSON to {storage_dir}/{id}.json.

        Args:
            note: The Note object to save.
        """
        self._ensure_storage_dir()
        file_path = os.path.join(self._storage_dir, f"{note.id}.json")
        json_str = self.serialize(note)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_str)

    def load_note(self, file_path: str) -> Optional[Note]:
        """Load a note from a JSON file.

        Args:
            file_path: Path to the JSON file to load.

        Returns:
            A Note object if the file was loaded successfully, or None
            if the file is corrupted or cannot be read.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_str = f.read()
            return self.deserialize(json_str)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error("Failed to load note from %s: %s", file_path, e)
            return None
        except OSError as e:
            logger.error("Failed to read note file %s: %s", file_path, e)
            return None

    def load_all_notes(self) -> List[Note]:
        """Load all notes from the storage directory.

        Iterates over all .json files in the storage directory and
        attempts to load each one. Corrupted files are skipped with
        an error logged.

        Returns:
            A list of successfully loaded Note objects.
        """
        self._ensure_storage_dir()
        notes: List[Note] = []
        for filename in os.listdir(self._storage_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self._storage_dir, filename)
                note = self.load_note(file_path)
                if note is not None:
                    notes.append(note)
        return notes

    def delete_note_file(self, note_id: str) -> None:
        """Remove a note's JSON file from disk.

        Args:
            note_id: The unique identifier of the note to delete.
        """
        file_path = os.path.join(self._storage_dir, f"{note_id}.json")
        try:
            os.remove(file_path)
        except OSError as e:
            logger.error("Failed to delete note file %s: %s", file_path, e)
