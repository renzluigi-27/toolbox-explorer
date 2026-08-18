"""
Toolbox Finder - File list panel (Details view)
Created by Renz Luigi - renzluigi.pages.dev

Shows files/folders in the selected directory as a table:
Name, Date modified, Type, Size. Supports sort and group by.
No thumbnails - details view only.
"""

import os
import datetime
import tkinter as tk
from tkinter import ttk


def format_size(num_bytes):
    if num_bytes is None:
        return ""
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def format_date(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%m/%d/%Y %I:%M %p")


def get_type_label(path, is_dir):
    if is_dir:
        return "File folder"
    ext = os.path.splitext(path)[1].lstrip(".").upper()
    return f"{ext} File" if ext else "File"


class FileListPanel(ttk.Frame):
    def __init__(self, parent, on_open_file=None, on_context_menu=None, ops=None, on_go_back=None, **kwargs):
        """
        ops: a context_menu.ContextMenu instance, used for keyboard shortcuts
             (Delete, F2, Ctrl+C/X/V) so they do the same thing as right-click.
        on_go_back: callback with no args, called on Backspace (go to parent folder)
        """
        super().__init__(parent, **kwargs)
        self.on_open_file = on_open_file
        self.on_context_menu = on_context_menu
        self.ops = ops
        self.on_go_back = on_go_back

        self.current_path = None
        self.sort_key = "date_modified"
        self.sort_reverse = True   # newest first, matches "Descending" default
        self.group_by = "date_modified"

        columns = ("date_modified", "type", "size")
        self.table = ttk.Treeview(self, columns=columns, show="tree headings")
        self.table.heading("#0", text="Name")
        self.table.heading("date_modified", text="Date modified")
        self.table.heading("type", text="Type")
        self.table.heading("size", text="Size")

        self.table.column("#0", width=320)
        self.table.column("date_modified", width=150)
        self.table.column("type", width=100)
        self.table.column("size", width=80, anchor="e")

        self.table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.table.yview)
        scrollbar.pack(side="right", fill="y")
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.bind("<Double-1>", self._on_double_click)
        self.table.bind("<Button-3>", self._on_right_click)  # right-click context menu

        # keyboard shortcuts, Windows Explorer style
        self.table.bind("<Delete>", self._on_key_delete)
        self.table.bind("<F2>", self._on_key_rename)
        self.table.bind("<Control-c>", self._on_key_copy)
        self.table.bind("<Control-x>", self._on_key_cut)
        self.table.bind("<Control-v>", self._on_key_paste)
        self.table.bind("<Return>", self._on_key_enter)
        self.table.bind("<F5>", self._on_key_refresh)
        self.table.bind("<BackSpace>", self._on_key_back)

    def load_folder(self, path):
        self.current_path = path
        self.table.delete(*self.table.get_children())

        try:
            entries = os.listdir(path)
        except (PermissionError, FileNotFoundError):
            return

        items = []
        for name in entries:
            full_path = os.path.join(path, name)
            try:
                stat = os.stat(full_path)
                is_dir = os.path.isdir(full_path)
                items.append({
                    "name": name,
                    "path": full_path,
                    "is_dir": is_dir,
                    "modified": stat.st_mtime,
                    "size": None if is_dir else stat.st_size,
                    "type": get_type_label(full_path, is_dir),
                })
            except (PermissionError, FileNotFoundError):
                continue

        items.sort(key=lambda i: i["modified"], reverse=self.sort_reverse)
        self._render_grouped(items)

    def _render_grouped(self, items):
        if self.group_by == "none":
            for item in items:
                self._insert_row(item)
            return

        groups = self._group_items(items)
        for label, group_items in groups.items():
            self.table.insert("", "end", text=label, open=True, tags=("group_header",))
            for item in group_items:
                self._insert_row(item)

        self.table.tag_configure("group_header", background="#e8e8e8")

    def _group_items(self, items):
        # groups by date bucket: Today, Yesterday, This week, Last week, Older
        now = datetime.datetime.now()
        buckets = {"Today": [], "Yesterday": [], "This week": [], "Last week": [], "Older": []}

        for item in items:
            dt = datetime.datetime.fromtimestamp(item["modified"])
            days_ago = (now.date() - dt.date()).days

            if days_ago == 0:
                buckets["Today"].append(item)
            elif days_ago == 1:
                buckets["Yesterday"].append(item)
            elif days_ago <= 7:
                buckets["This week"].append(item)
            elif days_ago <= 14:
                buckets["Last week"].append(item)
            else:
                buckets["Older"].append(item)

        return {k: v for k, v in buckets.items() if v}

    def _insert_row(self, item):
        icon_text = item["name"]  # icon handling can be added later
        self.table.insert(
            "", "end",
            text=icon_text,
            values=(
                format_date(item["modified"]),
                item["type"],
                format_size(item["size"]) if not item["is_dir"] else "",
            ),
            tags=(item["path"],),
        )

    def _on_double_click(self, event):
        node = self.table.focus()
        if not node:
            return
        tags = self.table.item(node, "tags")
        if tags and self.on_open_file:
            self.on_open_file(tags[0])

    def _on_right_click(self, event):
        node = self.table.identify_row(event.y)
        if not node:
            return
        self.table.selection_set(node)
        tags = self.table.item(node, "tags")
        if tags and self.on_context_menu:
            self.on_context_menu(tags[0], event.x_root, event.y_root)

    def _get_selected_path(self):
        node = self.table.focus()
        if not node:
            return None
        tags = self.table.item(node, "tags")
        return tags[0] if tags else None

    def _on_key_delete(self, event):
        path = self._get_selected_path()
        if path and self.ops:
            self.ops.delete(path)

    def _on_key_rename(self, event):
        path = self._get_selected_path()
        if path and self.ops:
            self.ops.rename(path)

    def _on_key_copy(self, event):
        path = self._get_selected_path()
        if path and self.ops:
            self.ops.copy(path)

    def _on_key_cut(self, event):
        path = self._get_selected_path()
        if path and self.ops:
            self.ops.move(path)

    def _on_key_paste(self, event):
        if self.current_path and self.ops:
            self.ops.paste(self.current_path)

    def _on_key_enter(self, event):
        path = self._get_selected_path()
        if path and self.on_open_file:
            self.on_open_file(path)

    def _on_key_refresh(self, event):
        if self.current_path:
            self.load_folder(self.current_path)

    def _on_key_back(self, event):
        if self.on_go_back:
            self.on_go_back()
