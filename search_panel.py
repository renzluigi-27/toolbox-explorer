"""
Toolbox Finder - Search panel
Created by Renz Luigi - renzluigi.pages.dev

Search bar + re-index button + results list.
Content indexing (xlsx/docx/pdf) can take a while on large folders,
so re-index runs in a background thread to keep the UI responsive.
"""

import os
import threading
import datetime
import tkinter as tk
from tkinter import ttk

import indexer


class SearchPanel(ttk.Frame):
    def __init__(self, parent, get_scope_path, on_open_file=None, **kwargs):
        """
        get_scope_path: callable returning the current search scope folder
        on_open_file: callback(path) when a result is double-clicked
        """
        super().__init__(parent, **kwargs)
        self.get_scope_path = get_scope_path
        self.on_open_file = on_open_file
        self.last_indexed_at = None
        self.cancel_event = None

        # ---- Search bar row ----
        bar = ttk.Frame(self)
        bar.pack(side="top", fill="x", padx=6, pady=4)

        self.query_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.query_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        entry.bind("<Return>", lambda e: self._run_search())

        search_btn = ttk.Button(bar, text="Search", command=self._run_search)
        search_btn.pack(side="left", padx=(0, 6))

        self.reindex_btn = ttk.Button(bar, text="Re-index", command=self._run_reindex)
        self.reindex_btn.pack(side="left")

        # ---- Progress bar (hidden until indexing starts) ----
        self.progress_frame = ttk.Frame(self)
        progress_row = ttk.Frame(self.progress_frame)
        progress_row.pack(side="top", fill="x", padx=6, pady=(0, 2))
        self.progress_bar = ttk.Progressbar(progress_row, mode="determinate")
        self.progress_bar.pack(side="left", fill="x", expand=True)
        self.cancel_btn = ttk.Button(progress_row, text="Cancel", command=self._cancel_reindex)
        self.cancel_btn.pack(side="left", padx=(6, 0))
        self.progress_label_var = tk.StringVar(value="")
        ttk.Label(self.progress_frame, textvariable=self.progress_label_var, foreground="#666").pack(
            side="top", anchor="w", padx=6, pady=(0, 4)
        )

        # ---- Results table ----
        columns = ("matched_in", "path")
        self.table = ttk.Treeview(self, columns=columns, show="tree headings")
        self.table.heading("#0", text="Name")
        self.table.heading("matched_in", text="Matched in")
        self.table.heading("path", text="Path")

        self.table.column("#0", width=280)
        self.table.column("matched_in", width=140)
        self.table.column("path", width=400)

        self.table.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 4))
        self.table.bind("<Double-1>", self._on_double_click)

        # ---- Status row ----
        self.status_var = tk.StringVar(value="")
        status_label = ttk.Label(self, textvariable=self.status_var, foreground="#666")
        status_label.pack(side="top", anchor="w", padx=6, pady=(0, 4))

    # ---- actions ----

    def _run_search(self):
        query = self.query_var.get().strip()
        if not query:
            return

        scope = self.get_scope_path()
        results = indexer.search(query, scope_path=scope)
        self._render_results(results)

    def _render_results(self, results):
        self.table.delete(*self.table.get_children())
        for r in results:
            self.table.insert(
                "", "end",
                text=r["filename"],
                values=(r["matched_in"], r["path"]),
                tags=(r["path"],),
            )
        self.status_var.set(self._status_text(len(results)))

    def _status_text(self, result_count):
        parts = [f"{result_count} result{'s' if result_count != 1 else ''} found"]
        if self.last_indexed_at:
            parts.append(f"Index last built {self.last_indexed_at}")
        return " \u00b7 ".join(parts)

    def _run_reindex(self):
        scope = self.get_scope_path()
        if not scope or not os.path.isdir(scope):
            return

        self.cancel_event = threading.Event()
        self.reindex_btn.config(state="disabled", text="Indexing...")
        self.progress_frame.pack(side="top", fill="x", after=self.table, before=None)
        self.progress_bar["value"] = 0
        self.progress_label_var.set("Starting...")

        thread = threading.Thread(target=self._reindex_worker, args=(scope,), daemon=True)
        thread.start()

    def _cancel_reindex(self):
        if self.cancel_event:
            self.cancel_event.set()
            self.progress_label_var.set("Cancelling...")
            self.cancel_btn.config(state="disabled")

    def _reindex_worker(self, scope):
        def progress_callback(current, total, filename):
            self.after(0, self._on_progress, current, total, filename)

        count, cancelled = indexer.build_index(
            scope, progress_callback=progress_callback, cancel_event=self.cancel_event
        )
        self.after(0, self._on_reindex_done, count, cancelled)

    def _on_progress(self, current, total, filename):
        if total:
            self.progress_bar["maximum"] = total
            self.progress_bar["value"] = current
        self.progress_label_var.set(f"Indexing files... {current} / {total or '?'}  \u00b7  Reading: {filename}")

    def _on_reindex_done(self, count, cancelled):
        self.last_indexed_at = datetime.datetime.now().strftime("%I:%M %p")
        self.reindex_btn.config(state="normal", text="Re-index")
        self.cancel_btn.config(state="normal")
        self.progress_frame.pack_forget()
        self.cancel_event = None

        if cancelled:
            self.status_var.set(f"Indexing cancelled \u00b7 {count} files indexed before stopping")
        else:
            self.status_var.set(f"Indexed {count} files \u00b7 Index last built {self.last_indexed_at}")

    def _on_double_click(self, event):
        node = self.table.focus()
        if not node:
            return
        tags = self.table.item(node, "tags")
        if tags and self.on_open_file:
            self.on_open_file(tags[0])
