"""
Modal and helper dialogs for NoteKeeper.
Includes New Notebook Wizard, About dialog, Word Count, and Global Search.
"""

import os
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable

from notekeeper.models.notebook import Notebook, NoteNode


class NewNotebookDialog(tk.Toplevel):
    """Dialog to create a new notebook directory."""

    def __init__(self, parent, on_created: Callable[[str], None]):
        super().__init__(parent)
        self.title("New Notebook")
        self.geometry("480x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_created = on_created
        default_dir = os.path.join(os.path.expanduser("~"), "Documents")

        self.dir_var = tk.StringVar(value=default_dir)
        self.name_var = tk.StringVar(value="New Notebook")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # Parent directory
        ttk.Label(self, text="Location:").grid(row=0, column=0, sticky="w", **pad)
        dir_frame = ttk.Frame(self)
        dir_frame.grid(row=0, column=1, sticky="ew", **pad)
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=32).pack(side="left", fill="x", expand=True)
        ttk.Button(dir_frame, text="Browse...", width=9, command=self._browse_dir).pack(side="left", padx=4)

        # Notebook name
        ttk.Label(self, text="Notebook Name:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.name_var, width=32).grid(row=1, column=1, sticky="w", **pad)

        # Full path preview
        self.preview_lbl = ttk.Label(self, text="", foreground="#666666", font=("Segoe UI", 8))
        self.preview_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        self.dir_var.trace_add("write", lambda *a: self._update_preview())
        self.name_var.trace_add("write", lambda *a: self._update_preview())
        self._update_preview()

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=16)
        ttk.Button(btn_frame, text="Create", width=12, command=self._create).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", width=12, command=self.destroy).pack(side="left", padx=6)

    def _browse_dir(self):
        chosen = filedialog.askdirectory(title="Select Folder for Notebook", initialdir=self.dir_var.get(), parent=self)
        if chosen:
            self.dir_var.set(chosen)

    def _update_preview(self):
        full = os.path.join(self.dir_var.get().strip(), self.name_var.get().strip())
        self.preview_lbl.config(text=f"Full path: {full}")

    def _create(self):
        parent_dir = self.dir_var.get().strip()
        name = self.name_var.get().strip()

        if not os.path.isdir(parent_dir):
            messagebox.showerror("Error", "Location directory does not exist!", parent=self)
            return
        if not name:
            messagebox.showerror("Error", "Please specify a notebook name.", parent=self)
            return

        try:
            nb = Notebook.create_new(parent_dir, name)
            self.on_created(nb.root_path)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create notebook: {e}", parent=self)


class AboutDialog(tk.Toplevel):
    """About NoteKeeper modal window."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("About NoteKeeper")
        self.geometry("450x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        # Header banner
        header = ttk.Frame(self, padding=16)
        header.pack(fill="x")

        ttk.Label(header, text="NoteKeeper", font=("Segoe UI", 18, "bold"), foreground="#0b57d0").pack()
        ttk.Label(header, text="Version 1.0.0 (Windows 11 Compatible)", font=("Segoe UI", 9)).pack(pady=2)

        desc = (
            "A modern, lightweight hierarchical note-taking application\n"
            "inspired by KeepNote, rewritten in modern Python 3.\n\n"
            "• 100% bidirectional KeepNote file compatibility (notebook.nbk, node.xml, page.html)\n"
            "• High-DPI Windows 11 desktop experience\n"
            "• Rich text formatting, instant search, and tabbed note viewer\n"
        )
        ttk.Label(self, text=desc, justify="center", font=("Segoe UI", 9)).pack(padx=20, pady=8)

        gh_btn = ttk.Label(self, text="GitHub: Ahmed-cpu-del/notekeeper", foreground="#0b57d0", cursor="hand2", font=("Segoe UI", 9, "underline"))
        gh_btn.pack(pady=4)
        gh_btn.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Ahmed-cpu-del/notekeeper"))

        ttk.Button(self, text="Close", width=12, command=self.destroy).pack(pady=12)


class WordCountDialog(tk.Toplevel):
    """Shows word and character statistics for a note."""

    def __init__(self, parent, text_content: str):
        super().__init__(parent)
        self.title("Note Statistics")
        self.geometry("320x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        words = len(text_content.split())
        chars_with_spaces = len(text_content)
        chars_no_spaces = len(text_content.replace(" ", "").replace("\n", "").replace("\r", ""))
        lines = len(text_content.splitlines())
        paragraphs = len([p for p in text_content.split("\n\n") if p.strip()])

        pad = {"padx": 16, "pady": 4}
        ttk.Label(self, text="Document Statistics", font=("Segoe UI", 11, "bold")).pack(pady=10)

        stats = [
            ("Words:", words),
            ("Characters (with spaces):", chars_with_spaces),
            ("Characters (no spaces):", chars_no_spaces),
            ("Lines:", lines),
            ("Paragraphs:", paragraphs),
        ]

        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=20)
        for i, (label, val) in enumerate(stats):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Label(frame, text=str(val), font=("Segoe UI", 9, "bold")).grid(row=i, column=1, sticky="e", padx=10, pady=2)

        ttk.Button(self, text="OK", width=10, command=self.destroy).pack(pady=12)
