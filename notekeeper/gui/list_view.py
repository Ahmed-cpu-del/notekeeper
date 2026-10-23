"""
Child Node List View for NoteKeeper (KeepNote top-right pane).
Displays child notes/folders in a multi-column sortable table.
"""

import time
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict, List

from notekeeper.models.notebook import NoteNode
from notekeeper.gui.icons import IconManager


class NodeListView(ttk.Frame):
    """Table view displaying children of the active node."""

    def __init__(
        self,
        master,
        on_node_open: Optional[Callable[[NoteNode], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_node_open = on_node_open
        self.current_node: Optional[NoteNode] = None
        self.row_to_node: Dict[str, NoteNode] = {}
        self.sort_column = "title"
        self.sort_desc = False

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        columns = ("title", "type", "created", "modified")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("title", text="Title", command=lambda: self._sort_by("title"))
        self.tree.heading("type", text="Type", command=lambda: self._sort_by("type"))
        self.tree.heading("created", text="Created", command=lambda: self._sort_by("created"))
        self.tree.heading("modified", text="Modified", command=lambda: self._sort_by("modified"))

        self.tree.column("title", width=250, minwidth=120)
        self.tree.column("type", width=90, minwidth=60)
        self.tree.column("created", width=140, minwidth=100)
        self.tree.column("modified", width=140, minwidth=100)

        self.tree.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.bind("<Double-1>", self._on_double_click)

    def set_active_node(self, node: Optional[NoteNode]):
        """Updates the list view with the children of the given node."""
        self.current_node = node
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.row_to_node.clear()

        if not self.current_node:
            return

        children = list(self.current_node.children)

        # Sort children
        def sort_key(n: NoteNode):
            if self.sort_column == "title":
                return n.title.lower()
            elif self.sort_column == "type":
                return "Folder" if n.is_folder else "Page"
            elif self.sort_column == "created":
                return n.created_time
            elif self.sort_column == "modified":
                return n.modified_time
            return n.order

        children.sort(key=sort_key, reverse=self.sort_desc)

        for child in children:
            node_type = "Folder" if child.is_folder else "Page"
            c_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(child.created_time)) if child.created_time else ""
            m_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(child.modified_time)) if child.modified_time else ""

            item_id = self.tree.insert(
                "",
                "end",
                values=(child.title, node_type, c_time, m_time)
            )
            self.row_to_node[item_id] = child

    def _sort_by(self, col: str):
        if self.sort_column == col:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_column = col
            self.sort_desc = False
        self.refresh()

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item and item in self.row_to_node:
            node = self.row_to_node[item]
            if self.on_node_open:
                self.on_node_open(node)
