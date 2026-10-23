"""Unit tests for NoteKeeper components."""

import os
import sys
import unittest
import tkinter as tk

# Ensure notekeeper package is importable
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from notekeeper.models.notebook import Notebook, NoteNode
from notekeeper.utils.html_parser import NoteHtmlParser
from notekeeper.gui.icons import IconManager


class TestComponents(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_icons(self):
        icons = [
            "folder", "folder_open", "page", "notebook",
            "new_page", "new_folder", "save", "bold", "italic",
            "underline", "strike", "color_fg", "color_bg",
            "list_bullet", "list_number", "link", "image", "date",
            "undo", "redo", "cut", "copy", "paste", "trash",
            "back", "forward", "up", "search"
        ]
        for name in icons:
            img = IconManager.get(name, 16)
            self.assertIsNotNone(img)

    def test_html_roundtrip(self):
        text_widget = tk.Text(self.root)
        NoteHtmlParser.setup_default_tags(text_widget)

        sample_html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Test Title</title></head>
<body>
<h2>Meeting Notes</h2>
<p>Discussing <b>quarterly goals</b> with team.</p>
<ul>
<li>Goal 1</li>
<li>Goal 2</li>
</ul>
</body></html>"""

        NoteHtmlParser.load_html_to_text(text_widget, sample_html)
        content = text_widget.get("1.0", "end-1c")
        self.assertIn("Meeting Notes", content)
        self.assertIn("quarterly goals", content)
        self.assertIn("Goal 1", content)

        exported = NoteHtmlParser.save_text_to_html(text_widget, "Test Title")
        self.assertIn("<h2>Meeting Notes</h2>", exported)
        self.assertIn("<b>quarterly goals</b>", exported)
        self.assertIn("<li>Goal 1</li>", exported)

    def test_load_existing_notebook(self):
        notes_dir = r"C:\Users\Ahmed Khaled\Documents\My Notes"
        if os.path.exists(notes_dir):
            nb = Notebook(notes_dir)
            self.assertIsNotNone(nb.root_node)
            self.assertGreater(len(nb.root_node.children), 0)
            # Test search
            results = nb.search("car")
            self.assertTrue(len(results) > 0)

    def test_notebook_crud_operations(self):
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        try:
            nb = Notebook.create_new(temp_dir, "Test Notebook")
            self.assertEqual(nb.title, "Test Notebook")
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "Test Notebook", "notebook.nbk")))

            # 1. Add child page
            child_page = nb.add_child(nb.root_node, "Meeting Minutes", is_folder=False)
            self.assertEqual(child_page.title, "Meeting Minutes")
            self.assertTrue(child_page.is_page)
            self.assertTrue(os.path.exists(child_page.content_file))

            # 2. Add child folder
            child_folder = nb.add_child(nb.root_node, "Projects", is_folder=True)
            self.assertEqual(child_folder.title, "Projects")
            self.assertTrue(child_folder.is_folder)

            # 3. Add note inside folder
            sub_page = nb.add_child(child_folder, "Project Alpha", is_folder=False)
            sub_page.set_content("<p>Secret rocket design plans</p>")
            sub_page.save_content()

            # 4. Search
            results = nb.search("rocket")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].title, "Project Alpha")

            # 5. Rename
            nb.rename_node(child_page, "Renamed Minutes")
            self.assertEqual(child_page.title, "Renamed Minutes")

            # 6. Delete
            nb.delete_node(child_page)
            self.assertNotIn(child_page, nb.root_node.children)
            self.assertFalse(os.path.exists(child_page.path))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_main_window_init(self):
        # Destroy setUp root to ensure single Tk instance
        self.root.destroy()
        IconManager.clear_cache()

        from notekeeper.gui.main_window import MainWindow
        app = MainWindow(initial_notebook_path=r"C:\Users\Ahmed Khaled\Documents\My Notes")
        self.assertIsNotNone(app.notebook)
        self.assertEqual(app.notebook.title.lower(), "my notes")
        # Ensure widgets initialized
        self.assertIsNotNone(app.tree_view)
        self.assertIsNotNone(app.list_view)
        self.assertIsNotNone(app.editor)
        app.destroy()


if __name__ == "__main__":
    unittest.main()
