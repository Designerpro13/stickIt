# Implementation Plan: Sticky Notes App

## Overview

This plan implements a Linux desktop sticky notes application using Python, GTK4 (via PyGObject), and Hypothesis for property-based testing. The implementation proceeds from data models and persistence through to UI components, wiring everything together incrementally.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create directory structure: `src/`, `tests/`, configuration files
  - Create `pyproject.toml` with dependencies: PyGObject, Hypothesis, pytest
  - Create `src/__init__.py`, `src/models.py`, `src/constants.py`
  - Define the `Note` dataclass in `src/models.py` with all fields (id, content, position_x, position_y, width, height, color, always_on_top, created_at, modified_at)
  - Define constants in `src/constants.py` (MIN_WIDTH=200, MIN_HEIGHT=150, DEFAULT_WIDTH=300, DEFAULT_HEIGHT=300, AUTOSAVE_DELAY_MS=2000, STORAGE_DIR, COLOR_PALETTE)
  - _Requirements: 3.2, 3.3, 6.1_

- [x] 2. Implement persistence store (serialization/deserialization)
  - [x] 2.1 Implement `PersistenceStore` class in `src/persistence.py`
    - Implement `serialize(note: Note) -> str` producing pretty-printed JSON
    - Implement `deserialize(json_str: str) -> Note` parsing JSON into Note object
    - Implement `save_note(note: Note)` writing to `~/.local/share/sticky-notes-app/notes/{id}.json`
    - Implement `load_note(file_path: str) -> Optional[Note]` with error handling for corrupted files
    - Implement `load_all_notes() -> List[Note]` iterating over storage directory
    - Implement `delete_note_file(note_id: str)` removing the JSON file
    - Handle missing storage directory by creating it on first access
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 2.2 Write property test for serialization round-trip
    - **Property 1: Serialization Round-Trip**
    - Generate arbitrary valid Note objects using Hypothesis strategies
    - Verify: `serialize(deserialize(serialize(note))) == serialize(note)`
    - Verify: `deserialize(serialize(note)) == note`
    - Minimum 100 iterations
    - **Validates: Requirements 4.5, 8.1, 8.2, 8.3, 8.4**

  - [ ]* 2.3 Write property test for corrupted data handling
    - **Property 6: Corrupted Data Graceful Handling**
    - Generate random invalid JSON strings using Hypothesis text strategy
    - Verify: deserialization does not raise unhandled exceptions
    - Verify: returns None or error indicator
    - Verify: error is logged
    - Minimum 100 iterations
    - **Validates: Requirements 8.5**

- [x] 3. Implement note manager core logic
  - [x] 3.1 Implement `NoteManager` class in `src/note_manager.py`
    - Implement `create_note() -> Note` generating UUID, setting defaults (300x300, yellow, position at center)
    - Implement `delete_note(note_id: str)` removing from active list and calling persistence delete
    - Implement `get_all_notes() -> List[Note]` returning active notes
    - Implement `restore_notes()` loading from persistence and populating active list
    - Implement `reposition_offscreen_note(note, screen_width, screen_height)` clamping position to visible area
    - _Requirements: 1.1, 1.2, 1.3, 6.3, 7.1, 7.2_

  - [ ]* 3.2 Write property test for unique ID generation
    - **Property 2: Unique ID Generation**
    - Create N notes (varying N with Hypothesis integers), verify all IDs are distinct
    - Minimum 100 iterations
    - **Validates: Requirements 1.3**

  - [ ]* 3.3 Write property test for note deletion
    - **Property 3: Note Deletion Removes from Manager and Store**
    - Generate random sets of notes, delete a randomly chosen note
    - Verify: deleted note not in `get_all_notes()`
    - Verify: deleted note file does not exist on disk
    - Minimum 100 iterations
    - **Validates: Requirements 1.2**

  - [ ]* 3.4 Write property test for off-screen position correction
    - **Property 5: Off-Screen Position Correction**
    - Generate random positions (including off-screen), random screen dimensions
    - Verify: after repositioning, note position is within (0, 0) to (screen_width - note_width, screen_height - note_height)
    - Verify: repositioned coordinates are the nearest valid position to original
    - Minimum 100 iterations
    - **Validates: Requirements 7.2**

- [x] 4. Checkpoint - Ensure core logic tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement resize constraint logic
  - [x] 5.1 Implement `apply_resize_constraints(width, height, screen_width, screen_height)` in `src/note_window.py`
    - Clamp width to [MIN_WIDTH, screen_width]
    - Clamp height to [MIN_HEIGHT, screen_height]
    - Return clamped (width, height) tuple
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 5.2 Write property test for resize dimension clamping
    - **Property 4: Resize Dimension Clamping**
    - Generate random target widths (0 to 10000) and heights (0 to 10000), random screen dimensions
    - Verify: result width in [200, screen_width] and height in [150, screen_height]
    - Minimum 100 iterations
    - **Validates: Requirements 3.2, 3.3**

- [x] 6. Implement rich text editor
  - [x] 6.1 Implement `RichTextEditor` class in `src/editor.py`
    - Extend Gtk.TextView with GtkTextBuffer tags for bold, italic, underline
    - Implement `apply_format(format_type, selection)` applying tag to selection range
    - Implement `get_content_as_html() -> str` exporting buffer as HTML
    - Implement `load_content_from_html(html: str)` parsing HTML into buffer with tags
    - Implement list formatting (bulleted and numbered) using indentation and markers
    - Implement font size support with size tags
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 6.2 Write property test for formatting preserves unselected content
    - **Property 7: Formatting Preserves Unselected Content**
    - Generate random text content and random selection ranges
    - Apply formatting to selection
    - Verify: text outside selection range is unchanged
    - Minimum 100 iterations
    - **Validates: Requirements 2.4**

- [x] 7. Implement note window (GTK4 UI)
  - [x] 7.1 Implement `NoteWindow` class in `src/note_window.py`
    - Create GTK4 window with window type hint for desktop widget (below other windows)
    - Add title bar with close button, color picker button, and pin (always-on-top) toggle
    - Embed RichTextEditor as main content area
    - Implement drag-to-move via title bar
    - Implement resize handles on edges and corners
    - Apply resize constraints on resize events
    - Connect content changes to debounced autosave (2-second delay)
    - _Requirements: 1.1, 1.4, 3.1, 5.1, 5.2, 5.4, 5.5_

  - [x] 7.2 Implement color picker in note window
    - Add color palette popup with predefined colors from COLOR_PALETTE
    - On color selection, update window background CSS and save to persistence
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 8. Implement application entry point and autostart
  - [x] 8.1 Implement `StickyNotesApp` in `src/main.py`
    - Create Gtk.Application subclass with unique app ID
    - On activate: call NoteManager.restore_notes(), create NoteWindow for each note
    - Add system tray indicator with "New Note" and "Quit" menu
    - Connect new note action to NoteManager.create_note() and spawn NoteWindow
    - Connect delete action from NoteWindow to NoteManager.delete_note()
    - Handle save errors by showing GTK notification
    - _Requirements: 1.1, 1.2, 4.2, 4.4, 5.3, 7.1_

  - [x] 8.2 Implement autostart desktop entry
    - Create `.desktop` file for `~/.config/autostart/`
    - Ensure app launches on Desktop_Session start
    - _Requirements: 5.3_

- [x] 9. Wire components together and final integration
  - [x] 9.1 Connect all components end-to-end
    - Wire NoteManager to PersistenceStore for save/load operations
    - Wire NoteWindow resize/move events to PersistenceStore.save_note()
    - Wire editor content changes to debounced PersistenceStore.save_note()
    - Wire color changes to PersistenceStore.save_note()
    - Verify note creation flow: button click → NoteManager.create_note() → NoteWindow appears with focus
    - Verify note deletion flow: close button → NoteManager.delete_note() → file removed
    - _Requirements: 1.1, 1.2, 1.4, 3.4, 4.1, 5.5, 6.4_

  - [ ]* 9.2 Write integration tests
    - Test full note lifecycle: create, edit, save, close, reopen, verify content
    - Test position persistence: move note, restart app, verify position
    - Test color persistence: change color, restart app, verify color
    - _Requirements: 4.2, 4.3, 5.5, 6.4, 7.1_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- The project uses Python with GTK4 (PyGObject) as determined by the design document
