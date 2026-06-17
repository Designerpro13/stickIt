# Requirements Document

## Introduction

A desktop sticky notes application for Linux that provides persistent, resizable notes that stick to the desktop. The application mimics the functionality of Windows Sticky Notes, allowing users to create, edit, and organize notes with rich text formatting and color customization. Notes persist across application restarts and system reboots, staying visible on the desktop at all times.

## Glossary

- **Application**: The Linux Sticky Notes desktop application
- **Note**: A single sticky note window displaying user-entered content
- **Note_Manager**: The core component responsible for creating, storing, and managing notes
- **Editor**: The rich text editing component within each note
- **Persistence_Store**: The component responsible for saving and loading note data to/from disk
- **Desktop_Session**: A user's active login session on the Linux desktop environment

## Requirements

### Requirement 1: Create and Delete Notes

**User Story:** As a user, I want to create and delete sticky notes, so that I can quickly capture and discard information on my desktop.

#### Acceptance Criteria

1. WHEN the user requests a new note, THE Note_Manager SHALL create a new Note with default dimensions of 300x300 pixels
2. WHEN the user requests to delete a note, THE Note_Manager SHALL remove the Note from the desktop and delete its persisted data
3. THE Note_Manager SHALL assign a unique identifier to each Note upon creation
4. WHEN a new Note is created, THE Editor SHALL place focus in the note body ready for text input

### Requirement 2: Rich Text Editing

**User Story:** As a user, I want to format my note text with rich text options, so that I can emphasize and organize information within a note.

#### Acceptance Criteria

1. THE Editor SHALL support bold, italic, and underline text formatting
2. THE Editor SHALL support bulleted and numbered lists
3. THE Editor SHALL support multiple font sizes
4. WHEN the user applies a formatting action, THE Editor SHALL apply the formatting to the selected text immediately
5. WHEN no text is selected, THE Editor SHALL apply formatting to text entered at the current cursor position

### Requirement 3: Note Resizing

**User Story:** As a user, I want to resize my notes, so that I can adjust them to fit varying amounts of content.

#### Acceptance Criteria

1. WHEN the user drags a note edge or corner, THE Note SHALL resize in the direction of the drag
2. THE Note SHALL enforce a minimum width of 200 pixels and a minimum height of 150 pixels
3. THE Note SHALL enforce a maximum width and height equal to the screen dimensions
4. WHEN a note is resized, THE Persistence_Store SHALL save the new dimensions

### Requirement 4: Note Persistence

**User Story:** As a user, I want my notes to persist across application restarts and system reboots, so that I never lose my captured information.

#### Acceptance Criteria

1. WHEN a Note's content changes, THE Persistence_Store SHALL save the content to disk within 2 seconds
2. WHEN the Application starts, THE Persistence_Store SHALL load all previously saved notes and restore them to their last known state
3. THE Persistence_Store SHALL save note content, position, dimensions, color, and formatting for each Note
4. IF the Persistence_Store fails to save a note, THEN THE Application SHALL display an error notification to the user
5. FOR ALL valid Note objects, saving then loading SHALL produce an equivalent Note object (round-trip property)

### Requirement 5: Desktop Stickiness

**User Story:** As a user, I want my notes to stay visible on the desktop at all times, so that I can always see my reminders regardless of other open windows.

#### Acceptance Criteria

1. THE Note SHALL remain visible on the desktop below normal application windows by default (desktop widget behavior)
2. WHEN the user activates "always on top" for a Note, THE Note SHALL remain above all other windows
3. WHEN the Desktop_Session starts, THE Application SHALL launch automatically and restore all notes
4. WHEN the user drags a note by its title bar, THE Note SHALL move to the new position on the desktop
5. WHEN a note is moved, THE Persistence_Store SHALL save the new position

### Requirement 6: Color Customization

**User Story:** As a user, I want to assign different colors to my notes, so that I can visually categorize and distinguish between notes.

#### Acceptance Criteria

1. THE Application SHALL provide a palette of at least 6 predefined note colors
2. WHEN the user selects a color from the palette, THE Note SHALL update its background color immediately
3. WHEN a new Note is created, THE Note_Manager SHALL assign the default color (yellow)
4. WHEN a note color is changed, THE Persistence_Store SHALL save the new color

### Requirement 7: Note Positioning

**User Story:** As a user, I want my notes to appear exactly where I left them, so that my desktop layout stays organized.

#### Acceptance Criteria

1. WHEN the Application restores notes on startup, THE Note_Manager SHALL place each Note at its last saved screen position
2. IF a saved position is off-screen (due to resolution change), THEN THE Note_Manager SHALL reposition the Note to the nearest visible screen edge
3. THE Note SHALL support free-form positioning anywhere on the desktop

### Requirement 8: Serialization and Deserialization

**User Story:** As a developer, I want a reliable storage format for notes, so that note data is never corrupted or lost.

#### Acceptance Criteria

1. THE Persistence_Store SHALL serialize Note data to JSON format
2. WHEN a serialized note file is read, THE Persistence_Store SHALL deserialize it into a valid Note object
3. THE Persistence_Store SHALL format Note objects into valid, human-readable JSON files (pretty printer)
4. FOR ALL valid Note objects, serializing then deserializing then serializing SHALL produce identical output (round-trip property)
5. IF a note file contains invalid or corrupted data, THEN THE Persistence_Store SHALL log the error and skip the corrupted note without crashing
