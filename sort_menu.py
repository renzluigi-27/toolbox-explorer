"""
Toolbox Finder - Sort / Group by menu
Created by Renz Luigi - renzluigi.pages.dev

Toolbar button that opens a Windows Explorer-style menu:
sort fields, ascending/descending, and a Group by submenu.
"""

import tkinter as tk
from tkinter import ttk


SORT_FIELDS = [
    ("name", "Name"),
    ("date_modified", "Date modified"),
    ("type", "Type"),
    ("size", "Size"),
]

GROUP_FIELDS = [
    ("name", "Name"),
    ("date_modified", "Date modified"),
    ("type", "Type"),
    ("size", "Size"),
    ("date_created", "Date created"),
    ("none", "(None)"),
]


class SortMenu(ttk.Frame):
    def __init__(self, parent, on_change=None, **kwargs):
        """
        on_change: callback(sort_key, sort_reverse, group_by) called
        whenever the user picks a new option.
        """
        super().__init__(parent, **kwargs)
        self.on_change = on_change

        self.sort_key = tk.StringVar(value="date_modified")
        self.sort_reverse = tk.BooleanVar(value=True)  # True = Descending
        self.group_by = tk.StringVar(value="date_modified")

        self.button = ttk.Button(self, text="Sort \u25be", command=self._show_menu)
        self.button.pack()

    def _show_menu(self):
        menu = tk.Menu(self, tearoff=0)

        for key, label in SORT_FIELDS:
            menu.add_radiobutton(
                label=label, value=key, variable=self.sort_key,
                command=self._notify,
            )

        menu.add_separator()
        menu.add_radiobutton(label="Ascending", value=False, variable=self.sort_reverse, command=self._notify)
        menu.add_radiobutton(label="Descending", value=True, variable=self.sort_reverse, command=self._notify)

        menu.add_separator()
        group_submenu = tk.Menu(menu, tearoff=0)
        for key, label in GROUP_FIELDS:
            group_submenu.add_radiobutton(
                label=label, value=key, variable=self.group_by,
                command=self._notify,
            )
        menu.add_cascade(label="Group by", menu=group_submenu)

        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height()
        menu.tk_popup(x, y)

    def _notify(self):
        if self.on_change:
            self.on_change(self.sort_key.get(), self.sort_reverse.get(), self.group_by.get())
