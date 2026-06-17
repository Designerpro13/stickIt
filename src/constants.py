"""Constants for the Sticky Notes application."""

import os

# Note dimension constraints
MIN_WIDTH: int = 200
MIN_HEIGHT: int = 150
DEFAULT_WIDTH: int = 300
DEFAULT_HEIGHT: int = 300

# Autosave delay in milliseconds
AUTOSAVE_DELAY_MS: int = 2000

# Storage directory following XDG Base Directory specification
STORAGE_DIR: str = os.path.expanduser("~/.local/share/sticky-notes-app/notes/")

# Color palette - predefined note colors
COLOR_PALETTE: dict[str, str] = {
    "yellow": "#FFEB3B",
    "green": "#C8E6C9",
    "blue": "#BBDEFB",
    "pink": "#F8BBD0",
    "purple": "#E1BEE7",
    "orange": "#FFE0B2",
    "white": "#FFFFFF",
    "gray": "#E0E0E0",
}

# Default color for new notes
DEFAULT_COLOR: str = "yellow"
