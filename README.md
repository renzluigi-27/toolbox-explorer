# ToolBox Explorer

A lightweight, portable Windows file explorer with fast filename **and file content** search — no install needed.

Built by [Renz Luigi](https://renzluigi.pages.dev)

---

## Why this exists

Windows' built-in Explorer++ is fast for browsing but only searches filenames. Windows' native Search can search file content too, but it's slower to set up per-folder and isn't portable.

ToolBox Explorer combines both: a fast, lightweight browser like Explorer++, plus a real search index (filenames **and** content inside `.xlsx`, `.docx`, and `.pdf` files) — all in a single portable `.exe`, no installation required.

## Features

- **Browse mode** — Details view (Name, Date modified, Type, Size), grouped by date modified, sortable, with a folder tree for quick navigation (Desktop, Downloads, Documents, Pictures, Music, Videos, This PC/drives)
- **Search mode** — filename + content search across `.xlsx`, `.xlsm`, `.docx`, and `.pdf` files, word-by-word matching like Windows Search
- **File operations** — Copy, Move, Rename, Delete (right-click or keyboard shortcuts)
- **Keyboard shortcuts** — Delete, F2 (rename), Ctrl+C/X/V (copy/cut/paste), Enter (open), F5 (refresh), Backspace (go back)
- **Portable** — single `.exe`, no installer, no registry changes
- **Lightweight** — no thumbnails, no real-time file watching, no background services

## Getting started

1. Download `ToolBoxExplorer.exe` from [Releases](../../releases)
2. Run it — no installation needed
3. **Browse mode works immediately** — no setup required
4. **Before using Search mode for the first time:**
   - Select a folder (via the tree or address bar)
   - Click **Search** to switch to Search mode
   - Click **Re-index** and wait for it to finish (a progress bar shows how far along it is)
   - Once done, you can search that folder's filenames and file content

> ⚠️ Search only works after indexing. If you search a folder before indexing it, you'll get no results.

Re-index again any time files in that folder change — the index doesn't update automatically.

## Keyboard shortcuts

| Key | Action |
|---|---|
| Delete | Delete selected file |
| F2 | Rename |
| Ctrl+C | Copy |
| Ctrl+X | Cut |
| Ctrl+V | Paste |
| Enter | Open |
| F5 | Refresh |
| Backspace | Go to parent folder |

## Building from source

Requires Python 3 with `openpyxl`, `python-docx`, and `pdfplumber` installed:

```
pip install openpyxl python-docx pdfplumber pyinstaller
```

Build the portable `.exe`:

```
python -m PyInstaller --onefile --windowed --icon=assets/icon.ico --add-data "assets;assets" --name "ToolBoxExplorer" main.py
```

Output: `dist/ToolBoxExplorer.exe`

## Notes

- The search index is stored separately from the app, at `%USERPROFILE%\.toolbox_finder\`, so rebuilding the `.exe` never affects your existing index.
- Content is only indexed for `.xlsx`, `.xlsm`, `.docx`, and `.pdf` files. Other file types are matched by filename only.

## License

Free to use.

---

Part of [Toolbox by Renz Luigi](https://renzluigi.pages.dev)
