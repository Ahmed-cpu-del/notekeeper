"""
Main Window for NoteKeeper.
Features the classic KeepNote 3-pane layout:
  - Left: Hierarchical TreeView
  - Top-Right: Child Node List View
  - Bottom-Right: Rich Text / HTML Note Editor
Plus top navigation toolbar, instant global search, and full menu system.
"""

import os
import sys
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, List

from notekeeper.config import ConfigManager
from notekeeper.models.notebook import Notebook, NoteNode
from notekeeper.gui.icons import IconManager
from notekeeper.gui.tree_view import NotebookTreeView
from notekeeper.gui.list_view import NodeListView
from notekeeper.gui.editor import NoteEditor
from notekeeper.gui.dialogs import NewNotebookDialog, AboutDialog, WordCountDialog


class MainWindow(tk.Tk):
    """NoteKeeper main desktop window."""

    def __init__(self, initial_notebook_path: Optional[str] = None):
        super().__init__()

        # Enable Windows 11 High-DPI awareness
        self._enable_dpi_awareness()

        self.title("NoteKeeper")
        self.geometry("1100x720")
        self.minsize(800, 500)

        self.config_mgr = ConfigManager()
        self.notebook: Optional[Notebook] = None

        # History navigation stacks
        self.history_back: List[str] = []
        self.history_forward: List[str] = []
        self._navigating_history = False

        self._build_panes()
        self._build_main_toolbar()
        self._build_status_bar()
        self._build_menus()
        self._setup_shortcuts()

        # Load notebook
        target_path = initial_notebook_path or self.config_mgr.get("last_notebook")
        if target_path and os.path.isdir(target_path):
            self.open_notebook_path(target_path)
        else:
            # Check default Documents/My Notes if present
            default_notes = os.path.join(os.path.expanduser("~"), "Documents", "My Notes")
            if os.path.isdir(default_notes):
                self.open_notebook_path(default_notes)

        # Restore window geometry
        geom = self.config_mgr.get("window_geometry")
        if geom:
            try:
                self.geometry(geom)
            except Exception:
                pass

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _enable_dpi_awareness(self):
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

    # ---------------- Menus ----------------

    def _build_menus(self):
        menubar = tk.Menu(self)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Notebook...", accelerator="Ctrl+Shift+O", command=self.show_new_notebook_dialog)
        file_menu.add_command(label="Open Notebook...", accelerator="Ctrl+O", command=self.browse_open_notebook)
        
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Notebooks", menu=self.recent_menu)
        self._update_recent_menu()

        file_menu.add_separator()
        file_menu.add_command(label="Save Note", accelerator="Ctrl+S", command=self.save_current)
        file_menu.add_command(label="Save All", accelerator="Ctrl+Shift+S", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="Close Notebook", command=self.close_notebook)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Alt+F4", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self._redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self._cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self._copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self._paste)
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self._select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find & Replace...", accelerator="Ctrl+F", command=self._show_find)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Refresh Tree", accelerator="F5", command=lambda: self.tree_view.refresh())
        menubar.add_cascade(label="View", menu=view_menu)

        # Note Menu
        note_menu = tk.Menu(menubar, tearoff=0)
        note_menu.add_command(label="New Page", accelerator="Ctrl+N", command=lambda: self.tree_view.new_child_page())
        note_menu.add_command(label="New Folder", accelerator="Ctrl+Shift+N", command=lambda: self.tree_view.new_child_folder())
        note_menu.add_separator()
        note_menu.add_command(label="Rename Node", accelerator="F2", command=lambda: self.tree_view.rename_selected())
        note_menu.add_command(label="Delete Node", accelerator="Del", command=lambda: self.tree_view.delete_selected())
        note_menu.add_separator()
        note_menu.add_command(label="Move Up", accelerator="Ctrl+Up", command=lambda: self.tree_view.move_node(-1))
        note_menu.add_command(label="Move Down", accelerator="Ctrl+Down", command=lambda: self.tree_view.move_node(1))
        menubar.add_cascade(label="Note", menu=note_menu)

        # Format Menu
        format_menu = tk.Menu(menubar, tearoff=0)
        format_menu.add_command(label="Bold", accelerator="Ctrl+B", command=lambda: self.editor.toggle_tag("bold"))
        format_menu.add_command(label="Italic", accelerator="Ctrl+I", command=lambda: self.editor.toggle_tag("italic"))
        format_menu.add_command(label="Underline", accelerator="Ctrl+U", command=lambda: self.editor.toggle_tag("underline"))
        format_menu.add_command(label="Strikethrough", command=lambda: self.editor.toggle_tag("strike"))
        format_menu.add_separator()
        format_menu.add_command(label="Text Color...", command=lambda: self.editor._choose_text_color())
        format_menu.add_command(label="Highlight Color...", command=lambda: self.editor._choose_bg_color())
        menubar.add_cascade(label="Format", menu=format_menu)

        # Insert Menu
        insert_menu = tk.Menu(menubar, tearoff=0)
        insert_menu.add_command(label="Bullet List", command=lambda: self.editor.insert_bullet_item())
        insert_menu.add_command(label="Numbered List", command=lambda: self.editor.insert_numbered_item())
        insert_menu.add_command(label="Horizontal Rule", command=lambda: self.editor.insert_horizontal_rule())
        insert_menu.add_separator()
        insert_menu.add_command(label="Insert Link...", accelerator="Ctrl+K", command=lambda: self.editor.show_insert_link_dialog())
        insert_menu.add_command(label="Insert Image...", command=lambda: self.editor.insert_image_file())
        insert_menu.add_command(label="Insert Date/Time", command=lambda: self.editor.insert_current_date())
        menubar.add_cascade(label="Insert", menu=insert_menu)

        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Word Count...", command=self.show_word_count)
        tools_menu.add_command(label="Open Notebook in Explorer", command=self.open_notebook_in_explorer)
        tools_menu.add_command(label="Open Current Note in Notepad", command=self.open_note_in_notepad)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="NoteKeeper on GitHub", command=lambda: webbrowser.open("https://github.com/Ahmed-cpu-del/notekeeper"))
        help_menu.add_separator()
        help_menu.add_command(label="About NoteKeeper", command=lambda: AboutDialog(self))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _update_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        recents = self.config_mgr.get_recent_notebooks()
        if not recents:
            self.recent_menu.add_command(label="(Empty)", state="disabled")
            return

        for path in recents:
            self.recent_menu.add_command(
                label=os.path.basename(path) + f"  ({path})",
                command=lambda p=path: self.open_notebook_path(p)
            )

    # ---------------- Main Toolbar ----------------

    def _build_main_toolbar(self):
        tb = ttk.Frame(self, padding=(4, 2, 4, 2))
        tb.pack(side="top", fill="x")

        # History Navigation buttons
        self.btn_back = ttk.Button(tb, image=IconManager.get("back", 16), width=3, command=self.nav_back)
        self.btn_back.pack(side="left", padx=1)
        self.btn_fwd = ttk.Button(tb, image=IconManager.get("forward", 16), width=3, command=self.nav_forward)
        self.btn_fwd.pack(side="left", padx=1)
        self.btn_up = ttk.Button(tb, image=IconManager.get("up", 16), width=3, command=self.nav_up_level)
        self.btn_up.pack(side="left", padx=1)

        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=4)

        # New Page / New Folder / Save
        ttk.Button(tb, image=IconManager.get("new_page", 16), width=3, command=lambda: self.tree_view.new_child_page()).pack(side="left", padx=1)
        ttk.Button(tb, image=IconManager.get("new_folder", 16), width=3, command=lambda: self.tree_view.new_child_folder()).pack(side="left", padx=1)
        ttk.Button(tb, image=IconManager.get("save", 16), width=3, command=self.save_current).pack(side="left", padx=1)

        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=4)

        # Cut, Copy, Paste, Undo, Redo
        ttk.Button(tb, image=IconManager.get("undo", 16), width=3, command=self._undo).pack(side="left", padx=1)
        ttk.Button(tb, image=IconManager.get("redo", 16), width=3, command=self._redo).pack(side="left", padx=1)
        ttk.Button(tb, image=IconManager.get("cut", 16), width=3, command=self._cut).pack(side="left", padx=1)
        ttk.Button(tb, image=IconManager.get("copy", 16), width=3, command=self._copy).pack(side="left", padx=1)
        ttk.Button(tb, image=IconManager.get("paste", 16), width=3, command=self._paste).pack(side="left", padx=1)

        # Search Bar on Far Right
        search_box = ttk.Frame(tb)
        search_box.pack(side="right", padx=4)

        ttk.Label(search_box, image=IconManager.get("search", 16)).pack(side="left", padx=2)
        self.search_entry = ttk.Entry(search_box, width=24)
        self.search_entry.pack(side="left", padx=2)
        self.search_entry.insert(0, "")
        self.search_entry.bind("<Return>", self._on_search_submitted)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        self.btn_clear_search = ttk.Button(search_box, text="✕", width=2, command=self._clear_search)
        self.btn_clear_search.pack(side="left", padx=1)

    # ---------------- 3-Pane Layout ----------------

    def _build_panes(self):
        # Master horizontal splitter: Left (Tree) | Right (List + Editor)
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True)

        # 1. Left Pane: Tree View
        tree_container = ttk.Frame(self.main_paned, width=260)
        self.tree_view = NotebookTreeView(
            tree_container,
            on_select_node=self._on_node_selected_in_tree,
            on_node_modified=self._on_structure_modified
        )
        self.tree_view.pack(fill="both", expand=True)
        self.main_paned.add(tree_container, weight=1)

        # 2. Right Pane: Vertical Splitter (List View on Top, Editor on Bottom)
        self.right_paned = ttk.PanedWindow(self.main_paned, orient="vertical")
        self.main_paned.add(self.right_paned, weight=4)

        # Top Right: Child List View
        list_container = ttk.Frame(self.right_paned, height=160)
        self.list_view = NodeListView(list_container, on_node_open=self._on_open_node_from_list)
        self.list_view.pack(fill="both", expand=True)
        self.right_paned.add(list_container, weight=1)

        # Bottom Right: Note Editor
        editor_container = ttk.Frame(self.right_paned, height=440)
        self.editor = NoteEditor(
            editor_container,
            on_navigate_node=self._on_navigate_node_id,
            on_note_title_changed=self._on_note_title_renamed
        )
        self.editor.pack(fill="both", expand=True)
        self.right_paned.add(editor_container, weight=3)

    # ---------------- Status Bar ----------------

    def _build_status_bar(self):
        self.status_bar = ttk.Frame(self, relief="sunken", padding=(6, 2, 6, 2))
        self.status_bar.pack(side="bottom", fill="x")

        self.status_path_lbl = ttk.Label(self.status_bar, text="Ready", font=("Segoe UI", 9))
        self.status_path_lbl.pack(side="left")

        self.status_count_lbl = ttk.Label(self.status_bar, text="", font=("Segoe UI", 9))
        self.status_count_lbl.pack(side="right")

    # ---------------- Event Handlers ----------------

    def _on_node_selected_in_tree(self, node: NoteNode):
        if not node:
            return

        # Record history if not currently traversing
        if not self._navigating_history:
            if not self.history_back or self.history_back[-1] != node.nodeid:
                self.history_back.append(node.nodeid)
                self.history_forward.clear()

        # Update List View
        self.list_view.set_active_node(node)

        # If it's a page or has content, open in editor
        if node.is_page:
            self.editor.open_node(node)

        # Update status bar path
        self._update_status_path(node)

    def _on_open_node_from_list(self, node: NoteNode):
        """When an item is double clicked in the child list view."""
        self.tree_view.select_node_by_id(node.nodeid)

    def _on_navigate_node_id(self, nodeid: str):
        """When a link like nbk:///<nodeid> is clicked inside a note."""
        self.tree_view.select_node_by_id(nodeid)

    def _on_note_title_renamed(self, node: NoteNode, new_title: str):
        self.tree_view.refresh()
        self.tree_view.select_node_by_id(node.nodeid)
        self.list_view.refresh()

    def _on_structure_modified(self):
        self.save_all()
        self._update_note_counts()

    def _update_status_path(self, node: NoteNode):
        crumbs = []
        curr = node
        while curr:
            crumbs.insert(0, curr.title)
            curr = curr.parent
        self.status_path_lbl.config(text=" > ".join(crumbs))

    def _update_note_counts(self):
        if not self.notebook:
            self.status_count_lbl.config(text="")
            return
        total = len(self.notebook.node_map)
        self.status_count_lbl.config(text=f"Total items: {total}")

    # ---------------- Navigation History ----------------

    def nav_back(self):
        if len(self.history_back) > 1:
            curr = self.history_back.pop()
            self.history_forward.append(curr)
            prev = self.history_back[-1]
            self._navigating_history = True
            self.tree_view.select_node_by_id(prev)
            self._navigating_history = False

    def nav_forward(self):
        if self.history_forward:
            nxt = self.history_forward.pop()
            self.history_back.append(nxt)
            self._navigating_history = True
            self.tree_view.select_node_by_id(nxt)
            self._navigating_history = False

    def nav_up_level(self):
        node = self.tree_view.get_selected_node()
        if node and node.parent:
            self.tree_view.select_node_by_id(node.parent.nodeid)

    # ---------------- Search ----------------

    def _on_search_submitted(self, event=None):
        query = self.search_entry.get().strip()
        if not query or not self.notebook:
            return

        results = self.notebook.search(query)
        if not results:
            messagebox.showinfo("Search", f"No notes found matching '{query}'.", parent=self)
            return

        # Show popup search results selector
        win = tk.Toplevel(self)
        win.title(f"Search Results: '{query}' ({len(results)} found)")
        win.geometry("500x320")
        win.transient(self)

        lbl = ttk.Label(win, text=f"Found {len(results)} notes matching '{query}':", font=("Segoe UI", 9, "bold"))
        lbl.pack(anchor="w", padx=10, pady=8)

        tree = ttk.Treeview(win, columns=("title", "type", "path"), show="headings", selectmode="browse")
        tree.heading("title", text="Title")
        tree.heading("type", text="Type")
        tree.heading("path", text="Path")
        tree.column("title", width=180)
        tree.column("type", width=70)
        tree.column("path", width=220)
        tree.pack(fill="both", expand=True, padx=10, pady=4)

        for res in results:
            t = "Folder" if res.is_folder else "Page"
            tree.insert("", "end", values=(res.title, t, res.path), iid=res.nodeid)

        def on_select(e=None):
            sel = tree.selection()
            if sel:
                node_id = sel[0]
                self.tree_view.select_node_by_id(node_id)
                win.destroy()

        tree.bind("<Double-1>", on_select)
        tree.bind("<Return>", on_select)

        btn_box = ttk.Frame(win)
        btn_box.pack(pady=8)
        ttk.Button(btn_box, text="Open Selected Note", command=on_select).pack(side="left", padx=4)
        ttk.Button(btn_box, text="Close", command=win.destroy).pack(side="left", padx=4)

    def _on_search_key(self, event=None):
        pass

    def _clear_search(self):
        self.search_entry.delete(0, tk.END)

    # ---------------- Notebook Loading / Operations ----------------

    def open_notebook_path(self, path: str):
        """Loads a KeepNote notebook folder into NoteKeeper."""
        if not os.path.isdir(path):
            return

        # Save any dirty note before switching
        self.save_all()

        try:
            self.notebook = Notebook(path)
            self.tree_view.set_notebook(self.notebook)
            self.config_mgr.add_recent_notebook(path)
            self._update_recent_menu()
            self.title(f"NoteKeeper - {self.notebook.title}")
            self._update_note_counts()

            # Select root or first child
            if self.notebook.root_node:
                first = self.notebook.root_node.children[0] if self.notebook.root_node.children else self.notebook.root_node
                self.tree_view.select_node_by_id(first.nodeid)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open notebook:\n{e}", parent=self)

    def browse_open_notebook(self):
        path = filedialog.askdirectory(title="Open Notebook Folder", parent=self)
        if path:
            self.open_notebook_path(path)

    def show_new_notebook_dialog(self):
        NewNotebookDialog(self, on_created=self.open_notebook_path)

    def close_notebook(self):
        self.save_all()
        self.notebook = None
        self.tree_view.set_notebook(None)
        self.list_view.set_active_node(None)
        self.title("NoteKeeper")
        self.status_path_lbl.config(text="No notebook open")
        self.status_count_lbl.config(text="")

    def save_current(self):
        self.editor.save_current_note()

    def save_all(self):
        self.editor.save_all_open()
        if self.notebook:
            self.notebook.save_all()

    # ---------------- Edit Helpers ----------------

    def _undo(self):
        if self.editor.current_tab:
            try:
                self.editor.current_tab.text_widget.edit_undo()
            except tk.TclError:
                pass

    def _redo(self):
        if self.editor.current_tab:
            try:
                self.editor.current_tab.text_widget.edit_redo()
            except tk.TclError:
                pass

    def _cut(self):
        if self.editor.current_tab:
            self.editor.current_tab.text_widget.event_generate("<<Cut>>")

    def _copy(self):
        if self.editor.current_tab:
            self.editor.current_tab.text_widget.event_generate("<<Copy>>")

    def _paste(self):
        if self.editor.current_tab:
            self.editor.current_tab.text_widget.event_generate("<<Paste>>")

    def _select_all(self):
        if self.editor.current_tab:
            t = self.editor.current_tab.text_widget
            t.tag_add(tk.SEL, "1.0", "end-1c")
            t.mark_set("insert", "1.0")
            t.see("insert")

    def _show_find(self):
        self.editor.show_find_bar()

    # ---------------- Tools ----------------

    def show_word_count(self):
        if self.editor.current_tab:
            content = self.editor.current_tab.text_widget.get("1.0", "end-1c")
            WordCountDialog(self, content)
        else:
            messagebox.showinfo("Word Count", "No note currently open.", parent=self)

    def open_notebook_in_explorer(self):
        if self.notebook and self.notebook.root_path and os.path.exists(self.notebook.root_path):
            subprocess.Popen(f'explorer "{self.notebook.root_path}"')

    def open_note_in_notepad(self):
        if self.editor.current_tab and self.editor.current_tab.node.is_page:
            path = self.editor.current_tab.node.content_file
            if os.path.exists(path):
                subprocess.Popen(f'notepad.exe "{path}"')

    # ---------------- Shortcuts ----------------

    def _setup_shortcuts(self):
        self.bind("<Control-s>", lambda e: self.save_current())
        self.bind("<Control-S>", lambda e: self.save_all())
        self.bind("<Control-o>", lambda e: self.browse_open_notebook())
        self.bind("<Control-O>", lambda e: self.show_new_notebook_dialog())
        self.bind("<Control-n>", lambda e: self.tree_view.new_child_page())
        self.bind("<Control-N>", lambda e: self.tree_view.new_child_folder())
        self.bind("<Control-f>", lambda e: self._show_find())
        self.bind("<Control-b>", lambda e: self.editor.toggle_tag("bold"))
        self.bind("<Control-i>", lambda e: self.editor.toggle_tag("italic"))
        self.bind("<Control-u>", lambda e: self.editor.toggle_tag("underline"))
        self.bind("<Control-k>", lambda e: self.editor.show_insert_link_dialog())
        self.bind("<Control-w>", lambda e: self.editor.close_current_tab())
        self.bind("<F5>", lambda e: self.tree_view.refresh())

    def _on_close(self):
        self.save_all()
        # Save geometry
        self.config_mgr.set("window_geometry", self.geometry())
        self.destroy()
