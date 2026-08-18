"""
Toolbox Finder
Created by Renz Luigi - renzluigi.pages.dev

Entry point. Wires together the directory tree, file list,
sort menu, and right-click context menu for Browse mode.
Search mode is added in a later piece.
"""

import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk

from directory_tree import DirectoryTree
from file_list import FileListPanel
from sort_menu import SortMenu
from context_menu import ContextMenu
from search_panel import SearchPanel


APP_TITLE = "ToolBox Explorer"
APP_AUTHOR = "Renz Luigi"
APP_URL = "https://renzluigi.pages.dev"


class ToolboxFinderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x600")
        self.minsize(800, 500)

        self.mode = "browse"
        self.current_path = os.path.expanduser("~")

        self._set_app_icon()
        self._build_layout()
        self._load_current_folder()

    def _set_app_icon(self):
        # works both running as a .py script and as a packaged .exe (PyInstaller)
        if hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(base_dir, "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                pass  # icon failed to load, app still runs fine without it

    def _build_layout(self):
        # ---- Toolbar ----
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x", padx=6, pady=4)

        self.address_var = tk.StringVar(value=self.current_path)
        address_entry = ttk.Entry(self.toolbar, textvariable=self.address_var)
        address_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        address_entry.bind("<Return>", self._on_address_enter)

        refresh_btn = ttk.Button(self.toolbar, text="Refresh", command=self._load_current_folder)
        refresh_btn.pack(side="left", padx=(0, 6))

        self.sort_menu = SortMenu(self.toolbar, on_change=self._on_sort_change)
        self.sort_menu.pack(side="left", padx=(0, 6))

        self.mode_btn = ttk.Button(self.toolbar, text="Search", command=self._toggle_mode)
        self.mode_btn.pack(side="left")

        # ---- Content: tree (left) + file list (right) ----
        self.content = ttk.PanedWindow(self, orient="horizontal")
        self.content.pack(side="top", fill="both", expand=True)

        self.tree = DirectoryTree(self.content, on_folder_select=self._on_folder_select)
        self.content.add(self.tree, weight=1)

        self.context_menu = ContextMenu(self, on_change=self._load_current_folder)

        self.file_list = FileListPanel(
            self.content,
            on_open_file=self._on_open_file,
            on_context_menu=self._on_context_menu,
            ops=self.context_menu,
            on_go_back=self._on_go_back,
        )
        self.content.add(self.file_list, weight=3)

        # Search panel lives in the same content area, hidden until Search mode
        self.search_panel = SearchPanel(
            self,
            get_scope_path=lambda: self.current_path,
            on_open_file=self._on_open_file,
        )

        # ---- Footer ----
        self.footer = ttk.Frame(self)
        self.footer.pack(side="bottom", fill="x", padx=6, pady=4)

        self.item_count_label = ttk.Label(self.footer, text="0 items")
        self.item_count_label.pack(side="left")

        credit = ttk.Label(
            self.footer,
            text=f"Created by {APP_AUTHOR} \u00b7 {APP_URL}",
            foreground="#1a6ec1",
            cursor="hand2",
        )
        credit.pack(side="right")
        credit.bind("<Button-1>", lambda e: webbrowser.open(APP_URL))

    # ---- event handlers ----

    def _load_current_folder(self):
        self.file_list.load_folder(self.current_path)
        self.address_var.set(self.current_path)
        count = len(self.file_list.table.get_children())
        self.item_count_label.config(text=f"{count} items")

    def _on_folder_select(self, path):
        self.current_path = path
        self._load_current_folder()

    def _on_address_enter(self, event):
        path = self.address_var.get()
        if os.path.isdir(path):
            self.current_path = path
            self._load_current_folder()

    def _on_sort_change(self, sort_key, sort_reverse, group_by):
        self.file_list.sort_key = sort_key
        self.file_list.sort_reverse = sort_reverse
        self.file_list.group_by = group_by
        self._load_current_folder()

    def _on_open_file(self, path):
        try:
            if os.path.isdir(path):
                self.current_path = path
                self._load_current_folder()
            else:
                os.startfile(path)  # Windows only
        except Exception as e:
            tk.messagebox.showerror("Open failed", str(e))

    def _on_context_menu(self, path, x, y):
        self.context_menu.show(path, x, y)

    def _on_go_back(self):
        parent = os.path.dirname(self.current_path.rstrip(os.sep))
        if parent and os.path.isdir(parent):
            self.current_path = parent
            self._load_current_folder()

    def _toggle_mode(self):
        if self.mode == "browse":
            self.mode = "search"
            self.content.pack_forget()
            self.search_panel.pack(side="top", fill="both", expand=True)
            self.mode_btn.config(text="Browse")
        else:
            self.mode = "browse"
            self.search_panel.pack_forget()
            self.content.pack(side="top", fill="both", expand=True)
            self.mode_btn.config(text="Search")


if __name__ == "__main__":
    app = ToolboxFinderApp()
    app.mainloop()
