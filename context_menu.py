"""
Toolbox Finder - Right-click context menu + file operations
Created by Renz Luigi - renzluigi.pages.dev

Handles Open, Copy, Move, Rename, Delete on a single file/folder.
Copy/Move use a simple clipboard-style flow: right-click Copy or Move,
then right-click a destination folder and choose Paste.
"""

import os
import shutil
import tkinter as tk
from tkinter import simpledialog, messagebox


class FileOpsClipboard:
    """Holds the path pending copy/move, and which action it was."""
    def __init__(self):
        self.path = None
        self.action = None  # "copy" or "move"

    def set(self, path, action):
        self.path = path
        self.action = action

    def clear(self):
        self.path = None
        self.action = None

    def has_item(self):
        return self.path is not None


clipboard = FileOpsClipboard()


class ContextMenu:
    def __init__(self, parent, on_change=None):
        """
        parent: the tk widget to attach the popup menu to
        on_change: callback to call after an operation, to refresh the file list
        """
        self.parent = parent
        self.on_change = on_change

    def show(self, path, x, y):
        menu = tk.Menu(self.parent, tearoff=0)
        is_dir = os.path.isdir(path)

        menu.add_command(label="Open", command=lambda: self.open(path))
        menu.add_separator()
        menu.add_command(label="Copy", command=lambda: self.copy(path))
        menu.add_command(label="Move", command=lambda: self.move(path))

        if clipboard.has_item() and is_dir:
            action_label = "Paste (copy here)" if clipboard.action == "copy" else "Paste (move here)"
            menu.add_command(label=action_label, command=lambda: self.paste(path))

        menu.add_command(label="Rename", command=lambda: self.rename(path))
        menu.add_separator()
        menu.add_command(label="Delete", command=lambda: self.delete(path))

        menu.tk_popup(x, y)

    def open(self, path):
        try:
            os.startfile(path)  # Windows only
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def copy(self, path):
        clipboard.set(path, "copy")

    def move(self, path):
        clipboard.set(path, "move")

    def paste(self, dest_folder):
        if not clipboard.has_item():
            return
        src = clipboard.path
        name = os.path.basename(src)
        dest = os.path.join(dest_folder, name)

        try:
            if clipboard.action == "copy":
                if os.path.isdir(src):
                    shutil.copytree(src, dest)
                else:
                    shutil.copy2(src, dest)
            elif clipboard.action == "move":
                shutil.move(src, dest)
                clipboard.clear()
        except Exception as e:
            messagebox.showerror("Paste failed", str(e))
        finally:
            if self.on_change:
                self.on_change()

    def rename(self, path):
        folder = os.path.dirname(path)
        old_name = os.path.basename(path)
        new_name = simpledialog.askstring("Rename", "New name:", initialvalue=old_name)

        if not new_name or new_name == old_name:
            return

        new_path = os.path.join(folder, new_name)
        try:
            os.rename(path, new_path)
        except Exception as e:
            messagebox.showerror("Rename failed", str(e))
        finally:
            if self.on_change:
                self.on_change()

    def delete(self, path):
        name = os.path.basename(path)
        confirm = messagebox.askyesno("Delete", f"Delete '{name}'? This cannot be undone.")
        if not confirm:
            return

        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as e:
            messagebox.showerror("Delete failed", str(e))
        finally:
            if self.on_change:
                self.on_change()
