"""
Toolbox Finder - Directory tree panel
Created by Renz Luigi - renzluigi.pages.dev

Left-side folder tree. Lazy-loads subfolders on expand
(does not scan the whole drive upfront - keeps it lightweight).
"""

import os
import string
import tkinter as tk
from tkinter import ttk


def get_drives():
    """Return list of available drives on Windows, e.g. ['C:\\\\', 'D:\\\\']"""
    drives = []
    for letter in string.ascii_uppercase:
        path = f"{letter}:\\"
        if os.path.exists(path):
            drives.append(path)
    return drives


class DirectoryTree(ttk.Frame):
    def __init__(self, parent, on_folder_select=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_folder_select = on_folder_select

        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewOpen>>", self._on_expand)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self._populate_root()

    def _populate_root(self):
        # Quick-access user folders, shown above This PC
        home = os.path.expanduser("~")
        quick_access = [
            ("Desktop", os.path.join(home, "Desktop")),
            ("Downloads", os.path.join(home, "Downloads")),
            ("Documents", os.path.join(home, "Documents")),
            ("Pictures", os.path.join(home, "Pictures")),
            ("Music", os.path.join(home, "Music")),
            ("Videos", os.path.join(home, "Videos")),
        ]
        for label, path in quick_access:
            if os.path.isdir(path):
                node = self.tree.insert("", "end", text=label, values=(path,))
                self._add_dummy_child(node)

        # "This PC" root node with drives under it, expanded by default
        this_pc = self.tree.insert("", "end", text="This PC", open=True, values=("__this_pc__",))
        for drive in get_drives():
            node = self.tree.insert(this_pc, "end", text=drive, values=(drive,))
            self._add_dummy_child(node)

    def _add_dummy_child(self, node):
        # Adds a placeholder child so the expand arrow shows up,
        # without scanning the folder yet (lazy load)
        self.tree.insert(node, "end", text="__loading__")

    def _on_expand(self, event):
        node = self.tree.focus()
        children = self.tree.get_children(node)

        # if the only child is our dummy placeholder, replace it with real folders
        if len(children) == 1 and self.tree.item(children[0], "text") == "__loading__":
            self.tree.delete(children[0])
            path = self.tree.item(node, "values")[0]
            self._load_subfolders(node, path)

    def _load_subfolders(self, node, path):
        try:
            entries = sorted(os.listdir(path))
        except (PermissionError, FileNotFoundError):
            return

        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                child = self.tree.insert(node, "end", text=entry, values=(full_path,))
                self._add_dummy_child(child)

    def _on_select(self, event):
        node = self.tree.focus()
        if not node:
            return
        values = self.tree.item(node, "values")
        if values and values[0] != "__this_pc__" and self.on_folder_select:
            self.on_folder_select(values[0])
