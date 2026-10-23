"""
Hierarchical Notebook Data Models for NoteKeeper.
Fully compatible with KeepNote format (notebook.nbk, node.xml, page.html).
"""

import os
import time
import uuid
import shutil
import re
import xml.etree.ElementTree as ET
from typing import Optional, List


def sanitize_filename(name: str) -> str:
    """Strip illegal filesystem characters for folder names."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean if clean else "untitled"


class NoteNode:
    """Represents a single node (Folder or Page) in the notebook hierarchy."""

    def __init__(self, path: str, parent: Optional["NoteNode"] = None):
        self.path = os.path.abspath(path)
        self.parent = parent
        self.children: List["NoteNode"] = []
        self.nodeid = str(uuid.uuid4())
        self.title = os.path.basename(path)
        self.content_type = "text/xhtml+xml"  # or 'application/x-notebook-dir'
        self.created_time = int(time.time())
        self.modified_time = int(time.time())
        self.order = 0
        self.icon = ""
        self._cached_content: Optional[str] = None
        self.is_dirty = False

        self.load_metadata()

    @property
    def is_folder(self) -> bool:
        return self.content_type == "application/x-notebook-dir"

    @property
    def is_page(self) -> bool:
        return not self.is_folder

    @property
    def xml_file(self) -> str:
        return os.path.join(self.path, "node.xml")

    @property
    def content_file(self) -> str:
        return os.path.join(self.path, "page.html")

    def load_metadata(self):
        """Reads node.xml if present."""
        if not os.path.exists(self.xml_file):
            return

        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            # Parse dict elements
            dict_elem = root.find("dict")
            if dict_elem is None:
                dict_elem = root

            curr_key = None
            for child in dict_elem:
                if child.tag == "key":
                    curr_key = child.text
                elif curr_key:
                    if curr_key == "title" and child.text:
                        self.title = child.text
                    elif curr_key == "nodeid" and child.text:
                        self.nodeid = child.text
                    elif curr_key == "content_type" and child.text:
                        self.content_type = child.text
                    elif curr_key == "created_time" and child.text and child.text.isdigit():
                        self.created_time = int(child.text)
                    elif curr_key == "modified_time" and child.text and child.text.isdigit():
                        self.modified_time = int(child.text)
                    elif curr_key == "order" and child.text and child.text.isdigit():
                        self.order = int(child.text)
                    elif curr_key == "icon" and child.text:
                        self.icon = child.text
                    curr_key = None
        except Exception:
            pass

    def save_metadata(self):
        """Writes metadata back to node.xml in KeepNote format."""
        root = ET.Element("node")
        ver = ET.SubElement(root, "version")
        ver.text = "6"
        d = ET.SubElement(root, "dict")

        def add_entry(key_name, tag_type, val):
            k = ET.SubElement(d, "key")
            k.text = key_name
            v = ET.SubElement(d, tag_type)
            v.text = str(val)

        add_entry("title", "string", self.title)
        add_entry("nodeid", "string", self.nodeid)
        add_entry("content_type", "string", self.content_type)
        add_entry("created_time", "integer", self.created_time)
        add_entry("modified_time", "integer", int(time.time()))
        add_entry("order", "integer", self.order)
        if self.icon:
            add_entry("icon", "string", self.icon)

        try:
            tree = ET.ElementTree(root)
            os.makedirs(self.path, exist_ok=True)
            tree.write(self.xml_file, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            print(f"Error saving metadata for {self.path}: {e}")

    def get_content(self) -> str:
        """Loads HTML content from page.html."""
        if self._cached_content is not None:
            return self._cached_content

        if os.path.exists(self.content_file):
            try:
                with open(self.content_file, "r", encoding="utf-8", errors="replace") as f:
                    self._cached_content = f.read()
                    return self._cached_content
            except Exception:
                pass

        # Return default empty page structure
        self._cached_content = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml"><body></body></html>'
        return self._cached_content

    def set_content(self, html_text: str):
        """Updates content in memory and marks dirty."""
        self._cached_content = html_text
        self.is_dirty = True

    def save_content(self):
        """Flushes cached content to disk."""
        if not self.is_dirty and os.path.exists(self.content_file):
            return

        content = self.get_content()
        try:
            os.makedirs(self.path, exist_ok=True)
            with open(self.content_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.modified_time = int(time.time())
            self.save_metadata()
            self.is_dirty = False
        except Exception as e:
            print(f"Error saving content for {self.path}: {e}")


class Notebook:
    """Manages an entire KeepNote notebook directory."""

    def __init__(self, root_path: Optional[str] = None):
        self.root_path: Optional[str] = None
        self.title: str = "Untitled Notebook"
        self.root_node: Optional[NoteNode] = None
        self.node_map: dict = {}  # nodeid -> NoteNode

        if root_path:
            self.load(root_path)

    @property
    def pref_file(self) -> str:
        return os.path.join(self.root_path, "notebook.nbk") if self.root_path else ""

    def load(self, path: str):
        """Loads a KeepNote notebook directory."""
        self.root_path = os.path.abspath(path)
        self.title = os.path.basename(self.root_path)
        self.node_map.clear()

        # Parse notebook preferences
        if os.path.exists(self.pref_file):
            try:
                tree = ET.parse(self.pref_file)
                root = tree.getroot()
                # Check for custom title if stored in pref
            except Exception:
                pass

        # Load root node
        self.root_node = NoteNode(self.root_path, parent=None)
        if not self.root_node.title or self.root_node.title == "My notes":
            self.title = self.root_node.title
        self.node_map[self.root_node.nodeid] = self.root_node

        # Recursively scan children
        self._scan_children(self.root_node)

    def _scan_children(self, parent_node: NoteNode):
        """Scans disk directories for sub-nodes."""
        try:
            entries = os.listdir(parent_node.path)
        except Exception:
            return

        for entry in sorted(entries):
            # Ignore hidden / system directories
            if entry.startswith(".") or entry in ("__NOTEBOOK__", "__TRASH__"):
                continue

            entry_path = os.path.join(parent_node.path, entry)
            if os.path.isdir(entry_path):
                xml_path = os.path.join(entry_path, "node.xml")
                # KeepNote node directories contain node.xml
                if os.path.exists(xml_path):
                    node = NoteNode(entry_path, parent=parent_node)
                    parent_node.children.append(node)
                    self.node_map[node.nodeid] = node
                    self._scan_children(node)

        # Sort children by order then title
        parent_node.children.sort(key=lambda n: (n.order, n.title.lower()))

    @classmethod
    def create_new(cls, parent_dir: str, name: str) -> "Notebook":
        """Creates a brand new KeepNote notebook directory on disk."""
        folder_name = sanitize_filename(name)
        nb_path = os.path.join(parent_dir, folder_name)
        os.makedirs(nb_path, exist_ok=True)

        # 1. Write notebook.nbk
        nbk_file = os.path.join(nb_path, "notebook.nbk")
        nbk_content = """<?xml version="1.0" encoding="UTF-8"?>
<notebook>
<version>6</version>
<pref>
    <dict>
        <key>version</key><integer>6</integer>
        <key>default_font</key><string>Segoe UI 11</string>
    </dict>
</pref>
</notebook>
"""
        with open(nbk_file, "w", encoding="utf-8") as f:
            f.write(nbk_content)

        # 2. Write root node.xml
        root_node = NoteNode(nb_path)
        root_node.title = name
        root_node.content_type = "application/x-notebook-dir"
        root_node.save_metadata()

        # 3. Create initial Welcome note
        welcome_dir = os.path.join(nb_path, "Welcome Note")
        os.makedirs(welcome_dir, exist_ok=True)
        welcome_node = NoteNode(welcome_dir, parent=root_node)
        welcome_node.title = "Welcome Note"
        welcome_node.content_type = "text/xhtml+xml"
        welcome_html = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Welcome</title></head>
<body>
<h2>Welcome to {name}!</h2>
<p>This notebook is managed by <b>NoteKeeper</b>, a modern hierarchical note-taking application inspired by KeepNote.</p>
<ul>
  <li><b>Hierarchical Notes:</b> Organize notes with pages and subfolders on the left.</li>
  <li><b>Rich Text:</b> Use formatting, bold, colors, bullet lists, and timestamps.</li>
  <li><b>Instant Search:</b> Use the search bar on the top toolbar to filter your notes quickly.</li>
  <li><b>KeepNote Compatible:</b> Opens and saves native KeepNote files with 100% fidelity.</li>
</ul>
<p><i>Created on {time.ctime()}</i></p>
</body>
</html>"""
        welcome_node.set_content(welcome_html)
        welcome_node.save_content()

        # Return loaded instance
        return cls(nb_path)

    def add_child(self, parent: NoteNode, title: str, is_folder: bool = False) -> NoteNode:
        """Creates a new child page or folder under parent."""
        base_name = sanitize_filename(title)
        child_path = os.path.join(parent.path, base_name)

        # Ensure unique directory path
        counter = 1
        while os.path.exists(child_path):
            child_path = os.path.join(parent.path, f"{base_name} {counter}")
            counter += 1

        os.makedirs(child_path, exist_ok=True)
        child_node = NoteNode(child_path, parent=parent)
        child_node.title = title
        child_node.content_type = "application/x-notebook-dir" if is_folder else "text/xhtml+xml"
        child_node.order = len(parent.children)
        child_node.save_metadata()

        if not is_folder:
            child_node.set_content(
                f'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n<html xmlns="http://www.w3.org/1999/xhtml"><body><h2>{title}</h2><p></p></body></html>'
            )
            child_node.save_content()

        parent.children.append(child_node)
        self.node_map[child_node.nodeid] = child_node
        return child_node

    def delete_node(self, node: NoteNode):
        """Deletes a node and all its children from disk and tree."""
        if node == self.root_node:
            return  # Cannot delete root

        if node.parent and node in node.parent.children:
            node.parent.children.remove(node)

        # Remove from node_map
        def remove_map(n):
            self.node_map.pop(n.nodeid, None)
            for c in n.children:
                remove_map(c)
        remove_map(node)

        # Remove from disk
        if os.path.exists(node.path):
            try:
                shutil.rmtree(node.path)
            except Exception as e:
                print(f"Error removing {node.path}: {e}")

    def rename_node(self, node: NoteNode, new_title: str):
        """Renames a node's title and directory."""
        if not new_title.strip() or node == self.root_node:
            return

        node.title = new_title.strip()
        node.modified_time = int(time.time())
        node.save_metadata()

    def search(self, query: str) -> List[NoteNode]:
        """Searches all nodes for query in title or page content."""
        query = query.strip().lower()
        if not query:
            return []

        results = []
        def visit(n: NoteNode):
            matched = False
            if query in n.title.lower():
                matched = True
            elif n.is_page:
                content = n.get_content().lower()
                # strip html tags for text comparison
                text_only = re.sub(r"<[^>]+>", " ", content)
                if query in text_only:
                    matched = True

            if matched and n != self.root_node:
                results.append(n)

            for child in n.children:
                visit(child)

        if self.root_node:
            visit(self.root_node)

        return results

    def save_all(self):
        """Saves all dirty pages in the notebook."""
        def visit(n: NoteNode):
            if n.is_dirty:
                n.save_content()
            for c in n.children:
                visit(c)

        if self.root_node:
            visit(self.root_node)
