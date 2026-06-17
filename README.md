# StickIt

A sticky notes application for Linux. Persistent, resizable, desktop-pinned notes with rich text and color customization. The Windows Sticky Notes experience, native on Linux.


## Features

- Create and delete notes on the fly
- Rich text editing (bold, italic, underline, lists, font sizes)
- Resizable with enforced min/max constraints
- Notes persist across restarts and reboots (JSON storage)
- Desktop widget mode (notes live below app windows by default)
- Always-on-top toggle per note
- 8-color palette for visual categorization
- Debounced autosave (2 seconds)
- Autostart on login
- Off-screen position correction on resolution changes


## Requirements

- Python 3.10+
- GTK4
- PyGObject


## Installation

```
# Install system dependencies (Arch/Manjaro)
sudo pacman -S gtk4 python-gobject

# Install system dependencies (Ubuntu/Debian)
sudo apt install libgtk-4-dev python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Install project
pip install -e .

# For development (includes pytest and hypothesis)
pip install -e ".[dev]"
```


## Usage

```
python3 -m src.main
```

Notes are stored as JSON files in `~/.local/share/sticky-notes-app/notes/`.


## Running Tests

```
python -m pytest tests/ -v
```


## Project Structure

```
src/
  main.py           - Application entry point (Gtk.Application)
  models.py         - Note dataclass
  constants.py      - Configuration constants and color palette
  persistence.py    - JSON file storage
  note_manager.py   - Note lifecycle management
  editor.py         - Rich text editor (GTK4 TextView + HTML serialization)
  note_window.py    - Note window UI with resize and drag
  color_picker.py   - Color palette popover
  autostart.py      - Desktop autostart management
data/
  sticky-notes-app.desktop - Freedesktop autostart entry
tests/
  test_persistence.py
  test_note_manager.py
  test_editor.py
  test_resize.py
  test_color_picker.py
docs/
  requirements.md   - Functional requirements
  design.md         - Architecture and technical design
  tasks.md          - Implementation plan
```


## License

MIT License. See LICENSE file.


---

Made with 🤍 and GTK4.
