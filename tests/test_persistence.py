"""Tests for the PersistenceStore class."""

import json
import os
import tempfile

import pytest

from src.models import Note
from src.persistence import PersistenceStore


@pytest.fixture
def tmp_storage(tmp_path):
    """Create a temporary storage directory for tests."""
    storage_dir = str(tmp_path / "notes")
    return storage_dir


@pytest.fixture
def store(tmp_storage):
    """Create a PersistenceStore with a temporary storage directory."""
    return PersistenceStore(storage_dir=tmp_storage)


class TestSerialize:
    """Tests for PersistenceStore.serialize."""

    def test_serialize_produces_valid_json(self, store):
        note = Note(id="test-id", content="Hello", position_x=10, position_y=20)
        result = store.serialize(note)
        data = json.loads(result)
        assert data["id"] == "test-id"
        assert data["content"] == "Hello"
        assert data["position_x"] == 10
        assert data["position_y"] == 20

    def test_serialize_pretty_prints_with_indent_2(self, store):
        note = Note(id="test-id", content="Hello")
        result = store.serialize(note)
        # Pretty-printed JSON with indent=2 should have lines starting with "  "
        lines = result.strip().split("\n")
        # At least some lines should start with 2-space indent
        indented_lines = [l for l in lines if l.startswith("  ")]
        assert len(indented_lines) > 0

    def test_serialize_includes_all_fields(self, store):
        note = Note()
        result = store.serialize(note)
        data = json.loads(result)
        expected_fields = {
            "id", "content", "position_x", "position_y",
            "width", "height", "color", "always_on_top",
            "created_at", "modified_at",
        }
        assert set(data.keys()) == expected_fields


class TestDeserialize:
    """Tests for PersistenceStore.deserialize."""

    def test_deserialize_produces_note_object(self, store):
        note = Note(id="abc", content="Test content", position_x=50, position_y=75)
        json_str = store.serialize(note)
        result = store.deserialize(json_str)
        assert isinstance(result, Note)
        assert result.id == "abc"
        assert result.content == "Test content"
        assert result.position_x == 50
        assert result.position_y == 75

    def test_deserialize_preserves_all_fields(self, store):
        note = Note(
            id="xyz",
            content="<b>bold</b>",
            position_x=100,
            position_y=200,
            width=400,
            height=500,
            color="blue",
            always_on_top=True,
            created_at="2024-01-01T00:00:00+00:00",
            modified_at="2024-06-15T12:30:00+00:00",
        )
        json_str = store.serialize(note)
        result = store.deserialize(json_str)
        assert result == note


class TestSaveNote:
    """Tests for PersistenceStore.save_note."""

    def test_save_creates_file(self, store, tmp_storage):
        note = Note(id="save-test")
        store.save_note(note)
        file_path = os.path.join(tmp_storage, "save-test.json")
        assert os.path.exists(file_path)

    def test_save_creates_storage_dir_if_missing(self, tmp_path):
        storage_dir = str(tmp_path / "nonexistent" / "dir" / "notes")
        store = PersistenceStore(storage_dir=storage_dir)
        note = Note(id="mkdir-test")
        store.save_note(note)
        assert os.path.isdir(storage_dir)

    def test_save_writes_valid_json(self, store, tmp_storage):
        note = Note(id="json-test", content="Content here")
        store.save_note(note)
        file_path = os.path.join(tmp_storage, "json-test.json")
        with open(file_path, "r") as f:
            data = json.load(f)
        assert data["id"] == "json-test"
        assert data["content"] == "Content here"


class TestLoadNote:
    """Tests for PersistenceStore.load_note."""

    def test_load_returns_note(self, store, tmp_storage):
        note = Note(id="load-test", content="Loaded")
        store.save_note(note)
        file_path = os.path.join(tmp_storage, "load-test.json")
        result = store.load_note(file_path)
        assert result is not None
        assert result.id == "load-test"
        assert result.content == "Loaded"

    def test_load_corrupted_returns_none(self, store, tmp_storage):
        os.makedirs(tmp_storage, exist_ok=True)
        file_path = os.path.join(tmp_storage, "corrupt.json")
        with open(file_path, "w") as f:
            f.write("not valid json {{{")
        result = store.load_note(file_path)
        assert result is None

    def test_load_missing_file_returns_none(self, store, tmp_storage):
        result = store.load_note(os.path.join(tmp_storage, "nonexistent.json"))
        assert result is None

    def test_load_invalid_fields_returns_none(self, store, tmp_storage):
        os.makedirs(tmp_storage, exist_ok=True)
        file_path = os.path.join(tmp_storage, "bad-fields.json")
        with open(file_path, "w") as f:
            json.dump({"unexpected_field": "value"}, f)
        result = store.load_note(file_path)
        assert result is None


class TestLoadAllNotes:
    """Tests for PersistenceStore.load_all_notes."""

    def test_load_all_empty_directory(self, store):
        notes = store.load_all_notes()
        assert notes == []

    def test_load_all_returns_saved_notes(self, store):
        note1 = Note(id="note-1", content="First")
        note2 = Note(id="note-2", content="Second")
        store.save_note(note1)
        store.save_note(note2)
        notes = store.load_all_notes()
        assert len(notes) == 2
        note_ids = {n.id for n in notes}
        assert note_ids == {"note-1", "note-2"}

    def test_load_all_skips_corrupted_files(self, store, tmp_storage):
        note = Note(id="good-note", content="OK")
        store.save_note(note)
        # Write a corrupted file
        corrupt_path = os.path.join(tmp_storage, "corrupt.json")
        with open(corrupt_path, "w") as f:
            f.write("invalid json")
        notes = store.load_all_notes()
        assert len(notes) == 1
        assert notes[0].id == "good-note"


class TestDeleteNoteFile:
    """Tests for PersistenceStore.delete_note_file."""

    def test_delete_removes_file(self, store, tmp_storage):
        note = Note(id="delete-me")
        store.save_note(note)
        file_path = os.path.join(tmp_storage, "delete-me.json")
        assert os.path.exists(file_path)
        store.delete_note_file("delete-me")
        assert not os.path.exists(file_path)

    def test_delete_nonexistent_does_not_crash(self, store):
        # Should not raise an exception
        store.delete_note_file("nonexistent-id")
