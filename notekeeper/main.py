"""
NoteKeeper - A modern, lightweight hierarchical note-taking application inspired by KeepNote.
Entry point.
"""

import sys
import os

# Ensure package root is in sys.path
package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if package_root not in sys.path:
    sys.path.insert(0, package_root)

from notekeeper.gui.main_window import MainWindow


def main():
    initial_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = MainWindow(initial_notebook_path=initial_path)
    app.mainloop()


if __name__ == "__main__":
    main()
