"""
Dynamic high-DPI icon generator for NoteKeeper.
Uses PIL to generate crisp icons in memory without requiring external asset files.
"""

import tkinter as tk
from typing import Dict, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageTk


class IconManager:
    """Generates and caches Tkinter PhotoImage icons."""
    _cache: Dict[Tuple[str, int], ImageTk.PhotoImage] = {}
    _current_master = None

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()
        cls._current_master = None

    @classmethod
    def get(cls, name: str, size: int = 16, master=None) -> ImageTk.PhotoImage:
        # If the active Tk root has changed, clear outdated photo image cache
        root = master or tk._default_root
        if root is not None and cls._current_master != root:
            cls._cache.clear()
            cls._current_master = root

        key = (name, size)
        if key in cls._cache:
            try:
                # Verify image is still valid in current Tcl interpreter
                _ = str(cls._cache[key])
                return cls._cache[key]
            except Exception:
                cls._cache.pop(key, None)

        img = cls._draw_icon(name, size)
        photo = ImageTk.PhotoImage(img, master=root)
        cls._cache[key] = photo
        return photo

    @classmethod
    def _draw_icon(cls, name: str, size: int) -> Image.Image:
        # Create a transparent RGBA image
        img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        # Scale factor
        s = size / 16.0

        def sc(val: float) -> int:
            return int(round(val * s))

        if name == "folder":
            # Folder tab
            draw.rectangle([sc(2), sc(3), sc(7), sc(6)], fill="#E5A93B")
            # Folder back
            draw.rectangle([sc(2), sc(5), sc(14), sc(13)], fill="#D99B26")
            # Folder front
            draw.polygon([
                (sc(1), sc(6)), (sc(14), sc(6)),
                (sc(13), sc(13)), (sc(2), sc(13))
            ], fill="#FFD05B", outline="#D99B26")

        elif name == "folder_open":
            draw.rectangle([sc(2), sc(2), sc(7), sc(5)], fill="#E5A93B")
            draw.rectangle([sc(2), sc(4), sc(14), sc(12)], fill="#D99B26")
            draw.polygon([
                (sc(0), sc(8)), (sc(15), sc(8)),
                (sc(13), sc(14)), (sc(2), sc(14))
            ], fill="#FFE082", outline="#D99B26")

        elif name == "page":
            # Document page with folded top-right corner
            draw.polygon([
                (sc(3), sc(1)), (sc(10), sc(1)),
                (sc(13), sc(4)), (sc(13), sc(14)),
                (sc(3), sc(14))
            ], fill="#FFFFFF", outline="#78909C")
            # Fold corner
            draw.polygon([
                (sc(10), sc(1)), (sc(10), sc(4)), (sc(13), sc(4))
            ], fill="#CFD8DC", outline="#78909C")
            # Text lines
            draw.line([sc(5), sc(6), sc(11), sc(6)], fill="#90A4AE", width=1)
            draw.line([sc(5), sc(8), sc(11), sc(8)], fill="#90A4AE", width=1)
            draw.line([sc(5), sc(10), sc(10), sc(10)], fill="#90A4AE", width=1)
            draw.line([sc(5), sc(12), sc(8), sc(12)], fill="#90A4AE", width=1)

        elif name == "notebook":
            # Notebook binder
            draw.rectangle([sc(3), sc(1), sc(14), sc(14)], fill="#1E88E5", outline="#1565C0")
            # Spine
            draw.rectangle([sc(2), sc(1), sc(5), sc(14)], fill="#0D47A1")
            # Rings
            for y in [sc(3), sc(6), sc(9), sc(12)]:
                draw.line([sc(1), y, sc(4), y], fill="#E0E0E0", width=1)
            # Label
            draw.rectangle([sc(7), sc(4), sc(12), sc(8)], fill="#FFFFFF")

        elif name == "new_page":
            # Page base
            draw.polygon([
                (sc(2), sc(1)), (sc(8), sc(1)),
                (sc(10), sc(3)), (sc(10), sc(12)),
                (sc(2), sc(12))
            ], fill="#FFFFFF", outline="#78909C")
            # Green Plus badge
            draw.rectangle([sc(7), sc(7), sc(15), sc(15)], fill="#4CAF50")
            draw.line([sc(11), sc(9), sc(11), sc(13)], fill="#FFFFFF", width=2)
            draw.line([sc(9), sc(11), sc(13), sc(11)], fill="#FFFFFF", width=2)

        elif name == "new_folder":
            # Folder base
            draw.rectangle([sc(2), sc(4), sc(6), sc(6)], fill="#E5A93B")
            draw.polygon([
                (sc(1), sc(6)), (sc(11), sc(6)),
                (sc(10), sc(13)), (sc(2), sc(13))
            ], fill="#FFD05B", outline="#D99B26")
            # Green Plus badge
            draw.rectangle([sc(8), sc(7), sc(15), sc(15)], fill="#4CAF50")
            draw.line([sc(11.5), sc(9), sc(11.5), sc(13)], fill="#FFFFFF", width=2)
            draw.line([sc(9.5), sc(11), sc(13.5), sc(11)], fill="#FFFFFF", width=2)

        elif name == "save":
            # Floppy disk
            draw.rectangle([sc(2), sc(2), sc(14), sc(14)], fill="#3F51B5", outline="#283593")
            # Metal slider
            draw.rectangle([sc(4), sc(2), sc(12), sc(6)], fill="#C5CAE9")
            # Label
            draw.rectangle([sc(4), sc(8), sc(12), sc(13)], fill="#FFFFFF")
            draw.line([sc(5), sc(10), sc(11), sc(10)], fill="#3F51B5", width=1)
            draw.line([sc(5), sc(12), sc(9), sc(12)], fill="#3F51B5", width=1)

        elif name == "bold":
            # Bold 'B'
            draw.line([sc(3), sc(2), sc(3), sc(13)], fill="#212121", width=3)
            draw.line([sc(3), sc(2), sc(9), sc(2)], fill="#212121", width=2)
            draw.line([sc(3), sc(7), sc(9), sc(7)], fill="#212121", width=2)
            draw.line([sc(3), sc(13), sc(9), sc(13)], fill="#212121", width=2)
            draw.arc([sc(6), sc(2), sc(12), sc(7)], 270, 90, fill="#212121", width=2)
            draw.arc([sc(6), sc(7), sc(12), sc(13)], 270, 90, fill="#212121", width=2)

        elif name == "italic":
            # Italic 'I'
            draw.line([sc(5), sc(2), sc(12), sc(2)], fill="#212121", width=2)
            draw.line([sc(4), sc(13), sc(11), sc(13)], fill="#212121", width=2)
            draw.line([sc(10), sc(2), sc(6), sc(13)], fill="#212121", width=2)

        elif name == "underline":
            # 'U' with underline
            draw.arc([sc(4), sc(2), sc(11), sc(10)], 0, 180, fill="#212121", width=2)
            draw.line([sc(4), sc(2), sc(4), sc(6)], fill="#212121", width=2)
            draw.line([sc(11), sc(2), sc(11), sc(6)], fill="#212121", width=2)
            draw.line([sc(3), sc(13), sc(12), sc(13)], fill="#212121", width=2)

        elif name == "strike":
            # 'S' with line through
            draw.text((sc(4), sc(0)), "S", fill="#212121")
            draw.line([sc(2), sc(8), sc(13), sc(8)], fill="#D32F2F", width=2)

        elif name == "color_fg":
            # 'A' with color bar
            draw.polygon([(sc(7), sc(1)), (sc(3), sc(11)), (sc(11), sc(11))], outline="#212121")
            draw.line([sc(5), sc(8), sc(9), sc(8)], fill="#212121", width=1)
            draw.rectangle([sc(2), sc(12), sc(13), sc(15)], fill="#E53935")

        elif name == "color_bg":
            # Highlighter marker
            draw.polygon([(sc(11), sc(2)), (sc(14), sc(5)), (sc(7), sc(12)), (sc(4), sc(9))], fill="#FFA000")
            draw.polygon([(sc(2), sc(14)), (sc(4), sc(9)), (sc(7), sc(12))], fill="#FFD54F")
            draw.rectangle([sc(2), sc(13), sc(14), sc(15)], fill="#FFEB3B")

        elif name == "list_bullet":
            # Bullet items
            for y in [sc(3), sc(7), sc(11)]:
                draw.ellipse([sc(2), y, sc(4), y + sc(2)], fill="#212121")
                draw.line([sc(6), y + sc(1), sc(14), y + sc(1)], fill="#424242", width=2)

        elif name == "list_number":
            # 1, 2, 3 items
            draw.text((sc(1), sc(1)), "1", fill="#212121")
            draw.line([sc(7), sc(4), sc(14), sc(4)], fill="#424242", width=1)
            draw.text((sc(1), sc(6)), "2", fill="#212121")
            draw.line([sc(7), sc(9), sc(14), sc(9)], fill="#424242", width=1)
            draw.text((sc(1), sc(11)), "3", fill="#212121")
            draw.line([sc(7), sc(13), sc(14), sc(13)], fill="#424242", width=1)

        elif name == "link":
            # Chain link
            draw.ellipse([sc(2), sc(4), sc(8), sc(10)], outline="#1976D2", width=2)
            draw.ellipse([sc(7), sc(4), sc(13), sc(10)], outline="#1976D2", width=2)

        elif name == "image":
            # Picture frame with mountain & sun
            draw.rectangle([sc(2), sc(2), sc(14), sc(13)], outline="#546E7A", width=1)
            draw.ellipse([sc(4), sc(4), sc(6), sc(6)], fill="#FDD835")
            draw.polygon([(sc(3), sc(12)), (sc(7), sc(7)), (sc(10), sc(11)), (sc(13), sc(8)), (sc(13), sc(12))], fill="#78909C")

        elif name == "date":
            # Calendar
            draw.rectangle([sc(2), sc(3), sc(13), sc(13)], outline="#D32F2F", width=1, fill="#FFFFFF")
            draw.rectangle([sc(2), sc(3), sc(13), sc(6)], fill="#D32F2F")
            draw.line([sc(4), sc(1), sc(4), sc(3)], fill="#212121", width=1)
            draw.line([sc(11), sc(1), sc(11), sc(3)], fill="#212121", width=1)

        elif name == "search":
            # Magnifying glass
            draw.ellipse([sc(3), sc(3), sc(10), sc(10)], outline="#212121", width=2)
            draw.line([sc(9), sc(9), sc(14), sc(14)], fill="#212121", width=2)

        elif name == "undo":
            # Curved arrow pointing left
            draw.arc([sc(3), sc(4), sc(13), sc(14)], 180, 360, fill="#212121", width=2)
            draw.polygon([(sc(1), sc(9)), (sc(6), sc(6)), (sc(6), sc(12))], fill="#212121")

        elif name == "redo":
            # Curved arrow pointing right
            draw.arc([sc(2), sc(4), sc(12), sc(14)], 180, 360, fill="#212121", width=2)
            draw.polygon([(sc(14), sc(9)), (sc(9), sc(6)), (sc(9), sc(12))], fill="#212121")

        elif name == "cut":
            # Scissors
            draw.ellipse([sc(2), sc(9), sc(6), sc(13)], outline="#212121", width=1)
            draw.ellipse([sc(8), sc(9), sc(12), sc(13)], outline="#212121", width=1)
            draw.line([sc(4), sc(10), sc(12), sc(2)], fill="#212121", width=2)
            draw.line([sc(10), sc(10), sc(2), sc(2)], fill="#212121", width=2)

        elif name == "copy":
            # Two sheets of paper
            draw.rectangle([sc(4), sc(2), sc(13), sc(11)], fill="#FFFFFF", outline="#78909C")
            draw.rectangle([sc(2), sc(5), sc(11), sc(14)], fill="#ECEFF1", outline="#546E7A")

        elif name == "paste":
            # Clipboard with paper
            draw.rectangle([sc(3), sc(3), sc(13), sc(14)], fill="#A1887F", outline="#6D4C41")
            draw.rectangle([sc(5), sc(5), sc(11), sc(13)], fill="#FFFFFF")
            draw.rectangle([sc(6), sc(1), sc(10), sc(4)], fill="#78909C")

        elif name == "trash":
            # Trash can
            draw.line([sc(2), sc(4), sc(13), sc(4)], fill="#D32F2F", width=2)
            draw.rectangle([sc(5), sc(2), sc(10), sc(4)], fill="#D32F2F")
            draw.polygon([(sc(3), sc(4)), (sc(12), sc(4)), (sc(10), sc(14)), (sc(5), sc(14))], fill="#EF5350")
            draw.line([sc(6), sc(6), sc(6), sc(12)], fill="#B71C1C", width=1)
            draw.line([sc(9), sc(6), sc(9), sc(12)], fill="#B71C1C", width=1)

        elif name == "back":
            draw.polygon([(sc(3), sc(8)), (sc(9), sc(3)), (sc(9), sc(13))], fill="#37474F")
            draw.line([sc(9), sc(8), sc(13), sc(8)], fill="#37474F", width=2)

        elif name == "forward":
            draw.polygon([(sc(13), sc(8)), (sc(7), sc(3)), (sc(7), sc(13))], fill="#37474F")
            draw.line([sc(3), sc(8), sc(7), sc(8)], fill="#37474F", width=2)

        elif name == "up":
            draw.polygon([(sc(8), sc(3)), (sc(3), sc(9)), (sc(13), sc(9))], fill="#37474F")
            draw.line([sc(8), sc(9), sc(8), sc(13)], fill="#37474F", width=2)

        else:
            # Generic bullet dot
            draw.ellipse([sc(4), sc(4), sc(12), sc(12)], fill="#757575")

        return img
