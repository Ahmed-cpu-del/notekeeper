"""
Rich Text Note Editor for NoteKeeper.
Provides full formatting toolbar, tabbed document interface, image/link embedding,
and KeepNote XHTML synchronization.
"""

import os
import shutil
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from typing import Optional, Callable, Dict, List

from notekeeper.models.notebook import NoteNode
from notekeeper.utils.html_parser import NoteHtmlParser
from notekeeper.gui.icons import IconManager


class NoteTab:
    """Represents a single open note tab inside the editor."""

    def __init__(self, node: NoteNode, frame: ttk.Frame, text_widget: tk.Text):
        self.node = node
        self.frame = frame
        self.text_widget = text_widget
        self.is_dirty = False


class NoteEditor(ttk.Frame):
    """Bottom-right pane containing tabs, formatting toolbar, and rich text editor."""

    def __init__(
        self,
        master,
        on_navigate_node: Optional[Callable[[str], None]] = None,
        on_note_title_changed: Optional[Callable[[NoteNode, str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_navigate_node = on_navigate_node
        self.on_note_title_changed = on_note_title_changed

        self.current_tab: Optional[NoteTab] = None
        self.open_tabs: Dict[str, NoteTab] = {}  # nodeid -> NoteTab

        self.font_family = tk.StringVar(value="Segoe UI")
        self.font_size = tk.StringVar(value="11")
        self.heading_var = tk.StringVar(value="Normal")

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Top note title bar
        self.title_frame = ttk.Frame(self, padding=(4, 4, 4, 2))
        self.title_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(self.title_frame, text="Note: ", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.title_entry = ttk.Entry(self.title_frame, font=("Segoe UI", 10, "bold"))
        self.title_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.title_entry.bind("<Return>", self._on_title_submitted)
        self.title_entry.bind("<FocusOut>", self._on_title_submitted)

        self.save_status_label = ttk.Label(self.title_frame, text="Saved", foreground="#555555", font=("Segoe UI", 8))
        self.save_status_label.pack(side="right", padx=6)

        # 2. Rich text formatting toolbar
        self._build_toolbar()

        # 3. Notebook Tabs
        self.tab_bar = ttk.Notebook(self)
        self.tab_bar.grid(row=2, column=0, sticky="nsew")
        self.tab_bar.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 4. Find & Replace bar (initially hidden)
        self._build_find_bar()

    def _build_toolbar(self):
        self.toolbar = ttk.Frame(self, padding=(2, 2, 2, 2))
        self.toolbar.grid(row=1, column=0, sticky="ew")

        # Headings combo
        self.heading_combo = ttk.Combobox(
            self.toolbar,
            textvariable=self.heading_var,
            values=["Normal", "Heading 1", "Heading 2", "Heading 3"],
            width=11,
            state="readonly"
        )
        self.heading_combo.pack(side="left", padx=2)
        self.heading_combo.bind("<<ComboboxSelected>>", lambda e: self._on_heading_changed())

        # Font Family combo
        fonts = ["Segoe UI", "Arial", "Calibri", "Consolas", "Courier New", "Georgia", "Tahoma", "Times New Roman", "Verdana"]
        self.font_combo = ttk.Combobox(self.toolbar, textvariable=self.font_family, values=fonts, width=13, state="readonly")
        self.font_combo.pack(side="left", padx=2)
        self.font_combo.bind("<<ComboboxSelected>>", lambda e: self._on_font_changed())

        # Font Size combo
        sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "36"]
        self.size_combo = ttk.Combobox(self.toolbar, textvariable=self.font_size, values=sizes, width=3, state="readonly")
        self.size_combo.pack(side="left", padx=2)
        self.size_combo.bind("<<ComboboxSelected>>", lambda e: self._on_font_changed())

        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=4)

        # Bold, Italic, Underline, Strike buttons
        self.btn_bold = ttk.Button(self.toolbar, image=IconManager.get("bold", 16), width=3, command=lambda: self.toggle_tag("bold"))
        self.btn_bold.pack(side="left", padx=1)

        self.btn_italic = ttk.Button(self.toolbar, image=IconManager.get("italic", 16), width=3, command=lambda: self.toggle_tag("italic"))
        self.btn_italic.pack(side="left", padx=1)

        self.btn_underline = ttk.Button(self.toolbar, image=IconManager.get("underline", 16), width=3, command=lambda: self.toggle_tag("underline"))
        self.btn_underline.pack(side="left", padx=1)

        self.btn_strike = ttk.Button(self.toolbar, image=IconManager.get("strike", 16), width=3, command=lambda: self.toggle_tag("strike"))
        self.btn_strike.pack(side="left", padx=1)

        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=4)

        # Text Color & Highlight buttons
        self.btn_color_fg = ttk.Button(self.toolbar, image=IconManager.get("color_fg", 16), width=3, command=self._choose_text_color)
        self.btn_color_fg.pack(side="left", padx=1)

        self.btn_color_bg = ttk.Button(self.toolbar, image=IconManager.get("color_bg", 16), width=3, command=self._choose_bg_color)
        self.btn_color_bg.pack(side="left", padx=1)

        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=4)

        # Lists & Alignment
        self.btn_bullet = ttk.Button(self.toolbar, image=IconManager.get("list_bullet", 16), width=3, command=self.insert_bullet_item)
        self.btn_bullet.pack(side="left", padx=1)

        self.btn_number = ttk.Button(self.toolbar, image=IconManager.get("list_number", 16), width=3, command=self.insert_numbered_item)
        self.btn_number.pack(side="left", padx=1)

        ttk.Separator(self.toolbar, orient="vertical").pack(side="left", fill="y", padx=4)

        # Insert Link, Image, Date/Time, Horizontal Rule
        self.btn_link = ttk.Button(self.toolbar, image=IconManager.get("link", 16), width=3, command=self.show_insert_link_dialog)
        self.btn_link.pack(side="left", padx=1)

        self.btn_image = ttk.Button(self.toolbar, image=IconManager.get("image", 16), width=3, command=self.insert_image_file)
        self.btn_image.pack(side="left", padx=1)

        self.btn_date = ttk.Button(self.toolbar, image=IconManager.get("date", 16), width=3, command=self.insert_current_date)
        self.btn_date.pack(side="left", padx=1)

    def _build_find_bar(self):
        self.find_frame = ttk.Frame(self, padding=(4, 2, 4, 2))
        ttk.Label(self.find_frame, text="Find:").pack(side="left", padx=2)
        self.find_entry = ttk.Entry(self.find_frame, width=20)
        self.find_entry.pack(side="left", padx=2)
        self.find_entry.bind("<Return>", lambda e: self.find_next())

        ttk.Label(self.find_frame, text="Replace:").pack(side="left", padx=4)
        self.replace_entry = ttk.Entry(self.find_frame, width=20)
        self.replace_entry.pack(side="left", padx=2)

        ttk.Button(self.find_frame, text="Find Next", command=self.find_next).pack(side="left", padx=2)
        ttk.Button(self.find_frame, text="Replace", command=self.replace_current).pack(side="left", padx=2)
        ttk.Button(self.find_frame, text="Replace All", command=self.replace_all).pack(side="left", padx=2)
        ttk.Button(self.find_frame, text="✕", width=2, command=self.hide_find_bar).pack(side="left", padx=4)

    def open_node(self, node: NoteNode):
        """Opens a node in an editor tab (or switches to existing tab)."""
        if not node:
            return

        # If already open, switch to that tab
        if node.nodeid in self.open_tabs:
            tab = self.open_tabs[node.nodeid]
            idx = self.tab_bar.index(tab.frame)
            self.tab_bar.select(idx)
            self.current_tab = tab
            self._update_title_bar(node)
            return

        # Otherwise create a new tab
        frame = ttk.Frame(self.tab_bar)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        text_widget = tk.Text(
            frame,
            wrap="word",
            undo=True,
            font=(self.font_family.get(), int(self.font_size.get())),
            padx=16,
            pady=16,
            relief="flat",
            highlightthickness=0,
            bg="#FFFFFF"
        )
        text_widget.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        text_widget.configure(yscrollcommand=v_scroll.set)

        # Setup tags
        NoteHtmlParser.setup_default_tags(
            text_widget,
            font_family=self.font_family.get(),
            font_size=int(self.font_size.get())
        )

        # Load content if page
        if node.is_page:
            content = node.get_content()
            NoteHtmlParser.load_html_to_text(
                text_widget,
                content,
                base_dir=node.path,
                on_link_click=self._handle_link_click
            )
        else:
            text_widget.insert("1.0", f"# {node.title}\n\n(This is a folder. You can add notes or subfolders inside it.)", ("h2",))

        # Reset modified state
        text_widget.edit_modified(False)
        text_widget.bind("<<Modified>>", lambda e, n=node: self._on_text_modified(n))

        # Add tab to ttk.Notebook
        tab_title = f"{node.title}  "
        self.tab_bar.add(frame, text=tab_title)
        self.tab_bar.select(frame)

        tab = NoteTab(node, frame, text_widget)
        self.open_tabs[node.nodeid] = tab
        self.current_tab = tab

        self._update_title_bar(node)

    def _update_title_bar(self, node: NoteNode):
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, node.title)
        self.save_status_label.config(text="Saved", foreground="#2e7d32")

    def _on_tab_changed(self, event):
        selected_id = self.tab_bar.select()
        if not selected_id:
            return

        for tab in self.open_tabs.values():
            if str(tab.frame) == selected_id:
                self.current_tab = tab
                self._update_title_bar(tab.node)
                break

    def _on_text_modified(self, node: NoteNode):
        if not self.current_tab or self.current_tab.node != node:
            return

        if self.current_tab.text_widget.edit_modified():
            self.current_tab.is_dirty = True
            node.is_dirty = True
            self.save_status_label.config(text="● Modified", foreground="#e65100")
            # Clear internal flag so subsequent changes fire event
            self.current_tab.text_widget.edit_modified(False)

    def _on_title_submitted(self, event=None):
        if not self.current_tab:
            return

        new_title = self.title_entry.get().strip()
        if new_title and new_title != self.current_tab.node.title:
            old_title = self.current_tab.node.title
            self.current_tab.node.title = new_title
            self.current_tab.node.modified_time = int(time.time())
            self.current_tab.node.save_metadata()

            # Update tab text
            idx = self.tab_bar.index(self.current_tab.frame)
            self.tab_bar.tab(idx, text=f"{new_title}  ")

            if self.on_note_title_changed:
                self.on_note_title_changed(self.current_tab.node, new_title)

    def save_current_note(self):
        """Saves current active note from Text widget back to KeepNote XHTML."""
        if not self.current_tab or not self.current_tab.node.is_page:
            return

        text_widget = self.current_tab.text_widget
        node = self.current_tab.node

        html_text = NoteHtmlParser.save_text_to_html(text_widget, title=node.title)
        node.set_content(html_text)
        node.save_content()

        self.current_tab.is_dirty = False
        self.save_status_label.config(text="Saved", foreground="#2e7d32")

    def save_all_open(self):
        """Saves all modified tabs."""
        for tab in self.open_tabs.values():
            if tab.is_dirty and tab.node.is_page:
                html_text = NoteHtmlParser.save_text_to_html(tab.text_widget, title=tab.node.title)
                tab.node.set_content(html_text)
                tab.node.save_content()
                tab.is_dirty = False

        if self.current_tab:
            self.save_status_label.config(text="Saved", foreground="#2e7d32")

    def close_current_tab(self):
        """Closes active tab after saving."""
        if not self.current_tab:
            return

        self.save_current_note()
        nodeid = self.current_tab.node.nodeid
        idx = self.tab_bar.index(self.current_tab.frame)
        self.tab_bar.forget(idx)
        self.open_tabs.pop(nodeid, None)

        if self.open_tabs:
            self._on_tab_changed(None)
        else:
            self.current_tab = None
            self.title_entry.delete(0, tk.END)
            self.save_status_label.config(text="")

    def _handle_link_click(self, href: str):
        """Handles clicking links inside note content."""
        if href.startswith("nbk:///"):
            # Internal notebook link! Format: nbk:///<nodeid>
            node_id = href[7:].strip()
            if self.on_navigate_node:
                self.on_navigate_node(node_id)
        elif href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:"):
            webbrowser.open(href)
        else:
            # Try opening local file or URL
            try:
                webbrowser.open(href)
            except Exception:
                pass

    # ---------------- Formatting Methods ----------------

    def toggle_tag(self, tag_name: str):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        try:
            sel_start = t.index(tk.SEL_FIRST)
            sel_end = t.index(tk.SEL_LAST)
        except tk.TclError:
            return  # No selection

        # Check if tag is currently on entire selection
        if tag_name in t.tag_names(sel_start):
            t.tag_remove(tag_name, sel_start, sel_end)
        else:
            t.tag_add(tag_name, sel_start, sel_end)

        self._on_text_modified(self.current_tab.node)

    def _choose_text_color(self):
        if not self.current_tab:
            return
        color = colorchooser.askcolor(title="Choose Text Color", parent=self)
        if color and color[1]:
            hex_color = color[1]
            self.apply_color(hex_color)

    def apply_color(self, hex_color: str):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        try:
            sel_start = t.index(tk.SEL_FIRST)
            sel_end = t.index(tk.SEL_LAST)
        except tk.TclError:
            return

        tag_name = f"fg_{hex_color}"
        t.tag_configure(tag_name, foreground=hex_color)
        t.tag_add(tag_name, sel_start, sel_end)
        self._on_text_modified(self.current_tab.node)

    def _choose_bg_color(self):
        if not self.current_tab:
            return
        color = colorchooser.askcolor(title="Choose Highlight Color", parent=self)
        if color and color[1]:
            hex_color = color[1]
            self.apply_bg_color(hex_color)

    def apply_bg_color(self, hex_color: str):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        try:
            sel_start = t.index(tk.SEL_FIRST)
            sel_end = t.index(tk.SEL_LAST)
        except tk.TclError:
            return

        tag_name = f"bg_{hex_color}"
        t.tag_configure(tag_name, background=hex_color)
        t.tag_add(tag_name, sel_start, sel_end)
        self._on_text_modified(self.current_tab.node)

    def _on_heading_changed(self):
        val = self.heading_var.get()
        tag_map = {"Normal": None, "Heading 1": "h1", "Heading 2": "h2", "Heading 3": "h3"}
        tag = tag_map.get(val)

        if not self.current_tab:
            return
        t = self.current_tab.text_widget

        # Apply to current line
        line_start = t.index("insert linestart")
        line_end = t.index("insert lineend")

        for h in ["h1", "h2", "h3"]:
            t.tag_remove(h, line_start, line_end)

        if tag:
            t.tag_add(tag, line_start, line_end)

        self._on_text_modified(self.current_tab.node)

    def _on_font_changed(self):
        if not self.current_tab:
            return
        fam = self.font_family.get()
        size = int(self.font_size.get())
        NoteHtmlParser.setup_default_tags(self.current_tab.text_widget, font_family=fam, font_size=size)
        self.current_tab.text_widget.configure(font=(fam, size))

    def insert_bullet_item(self):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        t.insert("insert", "• ", ("bullet",))
        self._on_text_modified(self.current_tab.node)

    def insert_numbered_item(self):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        t.insert("insert", "1. ", ("numbered",))
        self._on_text_modified(self.current_tab.node)

    def insert_horizontal_rule(self):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        t.insert("insert", "\n" + "—" * 60 + "\n", ("strike",))
        self._on_text_modified(self.current_tab.node)

    def insert_current_date(self):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        t.insert("insert", stamp)
        self._on_text_modified(self.current_tab.node)

    def show_insert_link_dialog(self):
        """Shows modal dialog to insert URL or link to another note."""
        if not self.current_tab:
            return

        t = self.current_tab.text_widget
        try:
            sel_text = t.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            sel_text = ""

        dialog = tk.Toplevel(self)
        dialog.title("Insert Link")
        dialog.geometry("380x160")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Link Text:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        text_ent = ttk.Entry(dialog, width=32)
        text_ent.insert(0, sel_text or "Link")
        text_ent.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(dialog, text="Target URL:").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        url_ent = ttk.Entry(dialog, width=32)
        url_ent.insert(0, "https://")
        url_ent.grid(row=1, column=1, padx=8, pady=8)

        def on_ok():
            txt = text_ent.get().strip()
            url = url_ent.get().strip()
            if not txt or not url:
                return

            if not hasattr(t, "_link_targets"):
                t._link_targets = {}

            link_tag = f"link_{int(time.time() * 1000)}"
            t._link_targets[link_tag] = url
            t.tag_configure(link_tag, foreground="#0b57d0", underline=True)
            t.tag_bind(link_tag, "<Button-1>", lambda e, h=url: self._handle_link_click(h))
            t.tag_bind(link_tag, "<Enter>", lambda e: t.config(cursor="hand2"))
            t.tag_bind(link_tag, "<Leave>", lambda e: t.config(cursor="xterm"))

            # If text was selected, replace it
            try:
                start = t.index(tk.SEL_FIRST)
                end = t.index(tk.SEL_LAST)
                t.delete(start, end)
                t.insert(start, txt, ("link", link_tag))
            except tk.TclError:
                t.insert("insert", txt, ("link", link_tag))

            self._on_text_modified(self.current_tab.node)
            dialog.destroy()

        btn_box = ttk.Frame(dialog)
        btn_box.grid(row=2, column=0, columnspan=2, pady=12)
        ttk.Button(btn_box, text="OK", command=on_ok).pack(side="left", padx=6)
        ttk.Button(btn_box, text="Cancel", command=dialog.destroy).pack(side="left", padx=6)

    def insert_image_file(self):
        """Selects an image file, copies into note folder, and embeds into note."""
        if not self.current_tab or not self.current_tab.node.is_page:
            return

        file_types = [("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All files", "*.*")]
        src_path = filedialog.askopenfilename(title="Select Image to Insert", filetypes=file_types, parent=self)
        if not src_path:
            return

        node = self.current_tab.node
        file_name = os.path.basename(src_path)
        dest_path = os.path.join(node.path, file_name)

        # Copy image file to note folder
        try:
            shutil.copy2(src_path, dest_path)
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to copy image: {e}", parent=self)
            return

        t = self.current_tab.text_widget
        from PIL import Image, ImageTk
        try:
            pil_img = Image.open(dest_path)
            max_w, max_h = 750, 600
            if pil_img.width > max_w or pil_img.height > max_h:
                pil_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)

            if not hasattr(t, "_embedded_images"):
                t._embedded_images = []
            t._embedded_images.append((tk_img, file_name))

            t.image_create("insert", image=tk_img)
            t.insert("insert", "\n")
            self._on_text_modified(node)
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to render image: {e}", parent=self)

    # ---------------- Find & Replace ----------------

    def show_find_bar(self):
        self.find_frame.grid(row=3, column=0, sticky="ew")
        self.find_entry.focus_set()
        self.find_entry.select_range(0, tk.END)

    def hide_find_bar(self):
        self.find_frame.grid_forget()

    def find_next(self):
        if not self.current_tab:
            return
        query = self.find_entry.get()
        if not query:
            return

        t = self.current_tab.text_widget
        start_idx = t.index("insert")
        pos = t.search(query, start_idx, stopindex=tk.END, nocase=True)
        if not pos:
            # Wrap around from top
            pos = t.search(query, "1.0", stopindex=start_idx, nocase=True)

        if pos:
            end_pos = f"{pos}+{len(query)}c"
            t.tag_remove(tk.SEL, "1.0", tk.END)
            t.tag_add(tk.SEL, pos, end_pos)
            t.mark_set("insert", end_pos)
            t.see(pos)
        else:
            messagebox.showinfo("Find", f"Pattern '{query}' not found.", parent=self)

    def replace_current(self):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        query = self.find_entry.get()
        replacement = self.replace_entry.get()
        if not query:
            return

        try:
            sel_start = t.index(tk.SEL_FIRST)
            sel_end = t.index(tk.SEL_LAST)
            if t.get(sel_start, sel_end).lower() == query.lower():
                t.delete(sel_start, sel_end)
                t.insert(sel_start, replacement)
                self._on_text_modified(self.current_tab.node)
        except tk.TclError:
            pass

        self.find_next()

    def replace_all(self):
        if not self.current_tab:
            return
        t = self.current_tab.text_widget
        query = self.find_entry.get()
        replacement = self.replace_entry.get()
        if not query:
            return

        count = 0
        curr = "1.0"
        while True:
            pos = t.search(query, curr, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(query)}c"
            t.delete(pos, end_pos)
            t.insert(pos, replacement)
            curr = f"{pos}+{len(replacement)}c"
            count += 1

        if count > 0:
            self._on_text_modified(self.current_tab.node)
            messagebox.showinfo("Replace All", f"Replaced {count} occurrences.", parent=self)
        else:
            messagebox.showinfo("Replace All", f"No occurrences of '{query}' found.", parent=self)
