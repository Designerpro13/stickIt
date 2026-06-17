"""Autostart management for Sticky Notes application.

Provides functions to install and uninstall the application's .desktop entry
in the user's ~/.config/autostart/ directory, ensuring the app launches
automatically on Desktop_Session start.
"""

import os
import shutil

# Name of the .desktop file
DESKTOP_ENTRY_FILENAME = "sticky-notes-app.desktop"

# Path to the source .desktop file in the project's data directory
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DESKTOP_FILE = os.path.join(_PROJECT_ROOT, "data", DESKTOP_ENTRY_FILENAME)

# XDG autostart directory
AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")


def get_autostart_path() -> str:
    """Return the full path where the .desktop file would be installed."""
    return os.path.join(AUTOSTART_DIR, DESKTOP_ENTRY_FILENAME)


def is_autostart_enabled() -> bool:
    """Check if the autostart desktop entry is currently installed."""
    return os.path.isfile(get_autostart_path())


def install_autostart() -> None:
    """Install the .desktop file to ~/.config/autostart/.

    Creates the autostart directory if it doesn't exist, then copies
    the desktop entry file so the application launches on session start.
    """
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    shutil.copy2(SOURCE_DESKTOP_FILE, get_autostart_path())


def uninstall_autostart() -> None:
    """Remove the .desktop file from ~/.config/autostart/.

    Silently succeeds if the file doesn't exist.
    """
    path = get_autostart_path()
    if os.path.isfile(path):
        os.remove(path)
