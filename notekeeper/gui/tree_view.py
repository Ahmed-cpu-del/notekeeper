"""
Hierarchical Notebook TreeView component for NoteKeeper.
Displays notebook nodes with folders, pages, and rich context menu operations.
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Callable, Dict

from notekeeper.models.notebook import Notebook, NoteNode
from notekeeper.gui.icons import IconManager


class NotebookTreeView(ttk.Frame):
    """Left pane tree view displaying the hierarchical note structure."""

    def __init__(
        self,
        master,
        on_select_node: Optional[Callable[[NoteNode], None]] = None,
        on_node_modified: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.notebook: Optional[Notebook] = None
        self.on_select_node = on_select_node
        self.on_node_modified = on_node_modified

        self.tree_to_node: Dict[str, NoteNode] = {}
        self.node_to_tree: Dict[str, str] = {}  # nodeid -> item_id

        self._build_ui()
        self._build_context_menu()

    def _build_ui(self):
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Style treeview
        style = ttk.Style()
        style.configure("Treeview", rowheight=22)

        self.tree = ttk.Treeview(self, selectmode="browse", show="tree")
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        # Event bindings
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<F2>", lambda e: self.rename_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())

    def _build_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="New Page",
            image=IconManager.get("new_page", 16),
            compound="left",
            command=self.new_child_page
        )
        self.context_menu.add_command(
            label="New Folder",
            image=IconManager.get("new_folder", 16),
            compound="left",
            command=self.new_child_folder
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Rename (F2)",
            command=self.rename_selected
        )
        self.context_menu.add_command(
            label="Delete (Del)",
            image=IconManager.get("trash", 16),
            compound="left",
            command=self.delete_selected
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Move Up",
            image=IconManager.get("up", 16),
            compound="left",
            command=lambda: self.move_node(-1)
        )
        self.context_menu.add_command(
            label="Move Down",
            command=lambda: self.move_node(1)
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Open Folder in File Explorer",
            command=self.open_in_explorer
        )
        self.context_menu.add_command(
            label="Copy Path",
            command=self.copy_path
        )

    def set_notebook(self, notebook: Optional[Notebook]):
        """Sets active notebook and rebuilds tree."""
        self.notebook = notebook
        self.refresh()

    def refresh(self):
        """Clears and reloads tree items from notebook hierarchy."""
        self.tree.delete(*self.tree.get_children())
        self.tree_to_node.clear()
        self.node_to_tree.clear()

        if not self.notebook or not self.notebook.root_node:
            return

        root_node = self.notebook.root_node
        root_icon = IconManager.get("notebook", 16)
        root_id = self.tree.insert("", "end", text=f" {root_node.title}", image=root_icon, open=True)
        self.tree_to_node[root_id] = root_node
        self.node_to_tree[root_node.nodeid] = root_id

        self._populate_node(root_id, root_node)
        self.tree.selection_set(root_id)

    def _populate_node(self, parent_tree_id: str, parent_node: NoteNode):
        for child in parent_node.children:
            if child.is_folder:
                icon = IconManager.get("folder", 16)
            else:
                icon = IconManager.get("page", 16)

            item_id = self.tree.insert(parent_tree_id, "end", text=f" {child.title}", image=icon, open=True)
            self.tree_to_node[item_id] = child
            self.node_to_tree[child.nodeid] = item_id

            if child.children:
                self._populate_node(item_id, child)

    def get_selected_node(self) -> Optional[NoteNode]:
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree_to_node.get(selected[0])

    def select_node_by_id(self, nodeid: str):
        """Programmatically select and reveal a node by its nodeid."""
        if nodeid in self.node_to_tree:
            item_id = self.node_to_tree[nodeid]
            self.tree.selection_set(item_id)
            self.tree.see(item_id)
            node = self.tree_to_node.get(item_id)
            if node and self.on_select_node:
                self.on_select_node(node)

    def _on_tree_select(self, event):
        node = self.get_selected_node()
        if node and self.on_select_node:
            self.on_select_node(node)

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def new_child_page(self):
        """Creates a new child note under the currently selected node."""
        parent = self.get_selected_node() or (self.notebook.root_node if self.notebook else None)
        if not parent or not self.notebook:
            return

        title = simpledialog.askstring("New Page", "Enter title for new note:", initialvalue="New Page", parent=self)
        if not title or not title.strip():
            return

        new_node = self.notebook.add_child(parent, title.strip(), is_folder=False)
        self.refresh()
        self.select_node_by_id(new_node.nodeid)
        if self.on_node_modified:
            self.on_node_modified()

    def new_child_folder(self):
        """Creates a new child folder under the currently selected node."""
        parent = self.get_selected_node() or (self.notebook.root_node if self.notebook else None)
        if not parent or not self.notebook:
            return

        title = simpledialog.askstring("New Folder", "Enter folder name:", initialvalue="New Folder", parent=self)
        if not title or not title.strip():
            return

        new_node = self.notebook.add_child(parent, title.strip(), is_folder=True)
        self.refresh()
        self.select_node_by_id(new_node.nodeid)
        if self.on_node_modified:
            self.on_node_modified()

    def rename_selected(self):
        """Renames the currently selected node."""
        node = self.get_selected_node()
        if not node or not self.notebook:
            return
        if node == self.notebook.root_node:
            messagebox.showinfo("Rename", "Cannot rename notebook root folder directly.", parent=self)
            return

        new_title = simpledialog.askstring("Rename Node", "Enter new title:", initialvalue=node.title, parent=self)
        if new_title and new_title.strip() and new_title.strip() != node.title:
            self.notebook.rename_node(node, new_title.strip())
            # Update treeview item text
            item_id = self.node_to_tree.get(node.nodeid)
            if item_id:
                self.tree.item(item_id, text=f" {node.title}")
            if self.on_node_modified:
                self.on_node_modified()

    def delete_selected(self):
        """Deletes the currently selected node after confirmation."""
        node = self.get_selected_node()
        if not node or not self.notebook:
            return
        if node == self.notebook.root_node:
            messagebox.showwarning("Delete", "Cannot delete notebook root!", parent=self)
            return

        kind = "folder and all its contents" if node.is_folder else "note"
        confirm = messagebox.askyesno(
            "Delete Confirmation",
            f"Are you sure you want to permanently delete {kind} '{node.title}'?",
            icon="warning",
            parent=self
        )
        if confirm:
            parent_id = node.parent.nodeid if node.parent else None
            self.notebook.delete_node(node)
            self.refresh()
            if parent_id:
                self.select_node_by_id(parent_id)
            if self.on_node_modified:
                self.on_node_modified()

    def move_node(self, direction: int):
        """Moves node up (-1) or down (+1) among its siblings."""
        node = self.get_selected_node()
        if not node or not node.parent or not self.notebook:
            return

        siblings = node.parent.children
        idx = siblings.index(node)
        new_idx = idx + direction
        if 0 <= new_idx < len(siblings):
            siblings[idx], siblings[new_idx] = siblings[new_idx], siblings[idx]
            # Update order attributes
            for i, sib in enumerate(siblings):
                sib.order = i
                sib.save_metadata()
            self.refresh()
            self.select_node_by_id(node.nodeid)
            if self.on_node_modified:
                self.on_node_modified()

    def open_in_explorer(self):
        """Opens node folder in Windows File Explorer."""
        node = self.get_selected_node()
        if node and os.path.exists(node.path):
            subprocess.Popen(f'explorer /select,"{node.path}"')

    def copy_path(self):
        """Copies the node filesystem path to clipboard."""
        node = self.get_selected_node()
        if node:
            self.clipboard_clear()
            self.clipboard_append(node.path)
