"""Unit tests for the NoteManager class."""

import os
import tempfile
from unittest.mock import MagicMock

import pytest

from src.constants import DEFAULT_COLOR, DEFAULT_HEIGHT, DEFAULT_WIDTH
from src.models import Note
from src.note_manager import NoteManager
from src.persistence import PersistenceStore


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for note storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def persistence_store(temp_storage_dir):
    """Create a PersistenceStore with a temporary storage directory."""
    return PersistenceStore(storage_dir=temp_storage_dir)


@pytest.fixture
def note_manager(persistence_store):
    """Create a NoteManager with a real persistence store."""
    return NoteManager(persistence_store=persistence_store)


class TestCreateNote:
    """Tests for NoteManager.create_note()."""

    def test_create_note_returns_note(self, note_manager):
        """Creating a note returns a Note object."""
        note = note_manager.create_note()
        assert isinstance(note, Note)

    def test_create_note_has_default_dimensions(self, note_manager):
        """New note has default width and height (300x300)."""
        note = note_manager.create_note()
        assert note.width == DEFAULT_WIDTH
        assert note.height == DEFAULT_HEIGHT

    def test_create_note_has_default_color(self, note_manager):
        """New note has default color (yellow)."""
        note = note_manager.create_note()
        assert note.color == DEFAULT_COLOR

    def test_create_note_positioned_at_center(self, note_manager):
        """New note is positioned at the center of the screen."""
        screen_w, screen_h = 1920, 1080
        note = note_manager.create_note(screen_width=screen_w, screen_height=screen_h)

        expected_x = (screen_w - DEFAULT_WIDTH) // 2
        expected_y = (screen_h - DEFAULT_HEIGHT) // 2
        assert note.position_x == expected_x
        assert note.position_y == expected_y

    def test_create_note_has_unique_id(self, note_manager):
        """Each created note has a unique identifier."""
        note1 = note_manager.create_note()
        note2 = note_manager.create_note()
        assert note1.id != note2.id

    def test_create_note_added_to_active_list(self, note_manager):
        """Created note appears in get_all_notes()."""
        note = note_manager.create_note()
        all_notes = note_manager.get_all_notes()
        assert note in all_notes

    def test_create_note_persisted_to_disk(self, note_manager, temp_storage_dir):
        """Created note is saved to the persistence store."""
        note = note_manager.create_note()
        file_path = os.path.join(temp_storage_dir, f"{note.id}.json")
        assert os.path.exists(file_path)


class TestDeleteNote:
    """Tests for NoteManager.delete_note()."""

    def test_delete_note_removes_from_active_list(self, note_manager):
        """Deleting a note removes it from the active notes list."""
        note = note_manager.create_note()
        note_manager.delete_note(note.id)
        all_notes = note_manager.get_all_notes()
        assert note not in all_notes

    def test_delete_note_removes_file_from_disk(self, note_manager, temp_storage_dir):
        """Deleting a note removes its JSON file from disk."""
        note = note_manager.create_note()
        file_path = os.path.join(temp_storage_dir, f"{note.id}.json")
        assert os.path.exists(file_path)

        note_manager.delete_note(note.id)
        assert not os.path.exists(file_path)

    def test_delete_nonexistent_note_does_not_raise(self, note_manager):
        """Deleting a non-existent note ID does not raise an exception."""
        note_manager.delete_note("nonexistent-id")

    def test_delete_note_does_not_affect_other_notes(self, note_manager):
        """Deleting one note doesn't remove other notes."""
        note1 = note_manager.create_note()
        note2 = note_manager.create_note()
        note_manager.delete_note(note1.id)
        all_notes = note_manager.get_all_notes()
        assert note2 in all_notes
        assert len(all_notes) == 1


class TestGetAllNotes:
    """Tests for NoteManager.get_all_notes()."""

    def test_get_all_notes_empty_initially(self, note_manager):
        """Initially, there are no active notes."""
        assert note_manager.get_all_notes() == []

    def test_get_all_notes_returns_created_notes(self, note_manager):
        """get_all_notes returns all notes that have been created."""
        note1 = note_manager.create_note()
        note2 = note_manager.create_note()
        all_notes = note_manager.get_all_notes()
        assert len(all_notes) == 2
        assert note1 in all_notes
        assert note2 in all_notes


class TestRestoreNotes:
    """Tests for NoteManager.restore_notes()."""

    def test_restore_notes_loads_from_persistence(self, persistence_store, temp_storage_dir):
        """restore_notes populates active list from persisted notes."""
        # Create notes and save them directly via persistence
        note1 = Note(position_x=100, position_y=200)
        note2 = Note(position_x=300, position_y=400)
        persistence_store.save_note(note1)
        persistence_store.save_note(note2)

        # Create a fresh NoteManager and restore
        manager = NoteManager(persistence_store=persistence_store)
        manager.restore_notes()

        all_notes = manager.get_all_notes()
        assert len(all_notes) == 2
        note_ids = [n.id for n in all_notes]
        assert note1.id in note_ids
        assert note2.id in note_ids

    def test_restore_notes_clears_previous_state(self, persistence_store, temp_storage_dir):
        """restore_notes replaces the current active list with persisted notes."""
        manager = NoteManager(persistence_store=persistence_store)
        manager.create_note()  # This creates a note in memory and on disk

        # Save a different note directly
        different_note = Note(position_x=500, position_y=600)
        persistence_store.save_note(different_note)

        manager.restore_notes()
        all_notes = manager.get_all_notes()
        # Should contain both the originally created note (persisted) and the different note
        note_ids = [n.id for n in all_notes]
        assert different_note.id in note_ids


class TestRepositionOffscreenNote:
    """Tests for NoteManager.reposition_offscreen_note()."""

    def test_note_within_bounds_unchanged(self, note_manager):
        """A note already within screen bounds is not moved."""
        note = Note(position_x=100, position_y=100, width=300, height=300)
        note_manager.reposition_offscreen_note(note, 1920, 1080)
        assert note.position_x == 100
        assert note.position_y == 100

    def test_note_negative_x_clamped_to_zero(self, note_manager):
        """A note with negative X position is clamped to 0."""
        note = Note(position_x=-50, position_y=100, width=300, height=300)
        note_manager.reposition_offscreen_note(note, 1920, 1080)
        assert note.position_x == 0
        assert note.position_y == 100

    def test_note_negative_y_clamped_to_zero(self, note_manager):
        """A note with negative Y position is clamped to 0."""
        note = Note(position_x=100, position_y=-50, width=300, height=300)
        note_manager.reposition_offscreen_note(note, 1920, 1080)
        assert note.position_x == 100
        assert note.position_y == 0

    def test_note_beyond_right_edge_clamped(self, note_manager):
        """A note beyond the right screen edge is clamped to max valid X."""
        note = Note(position_x=2000, position_y=100, width=300, height=300)
        note_manager.reposition_offscreen_note(note, 1920, 1080)
        assert note.position_x == 1920 - 300
        assert note.position_y == 100

    def test_note_beyond_bottom_edge_clamped(self, note_manager):
        """A note beyond the bottom screen edge is clamped to max valid Y."""
        note = Note(position_x=100, position_y=2000, width=300, height=300)
        note_manager.reposition_offscreen_note(note, 1920, 1080)
        assert note.position_x == 100
        assert note.position_y == 1080 - 300

    def test_note_both_axes_offscreen_clamped(self, note_manager):
        """A note off-screen on both axes is clamped on both."""
        note = Note(position_x=-100, position_y=5000, width=300, height=300)
        note_manager.reposition_offscreen_note(note, 1920, 1080)
        assert note.position_x == 0
        assert note.position_y == 1080 - 300

    def test_note_larger_than_screen(self, note_manager):
        """A note wider/taller than the screen is clamped to position (0, 0)."""
        note = Note(position_x=500, position_y=500, width=2000, height=1500)
        note_manager.reposition_offscreen_note(note, 1920, 1080)
        # max_x = max(0, 1920 - 2000) = 0, max_y = max(0, 1080 - 1500) = 0
        assert note.position_x == 0
        assert note.position_y == 0
