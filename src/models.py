"""Data models for the Sticky Notes application."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Note:
    """Represents a single sticky note with all its properties.

    Attributes:
        id: Unique identifier (UUID string).
        content: HTML-formatted rich text content.
        position_x: X coordinate on screen in pixels.
        position_y: Y coordinate on screen in pixels.
        width: Note width in pixels.
        height: Note height in pixels.
        color: Color key from the palette (e.g., 'yellow', 'blue').
        always_on_top: Whether the note stays above all other windows.
        created_at: ISO 8601 timestamp of when the note was created.
        modified_at: ISO 8601 timestamp of when the note was last modified.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    position_x: int = 0
    position_y: int = 0
    width: int = 300
    height: int = 300
    color: str = "yellow"
    always_on_top: bool = False
    opacity: float = 1.0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    modified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
