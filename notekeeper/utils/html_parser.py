"""
Bidirectional HTML/XHTML Parser for NoteKeeper and KeepNote notes.
Converts KeepNote XHTML <-> Tkinter Text widget styling and structure.
"""

import os
import re
import html
import tkinter as tk
from typing import Dict, List, Optional, Tuple, Callable
import bs4
from PIL import Image, ImageTk


class NoteHtmlParser:
    """Handles parsing XHTML into Tkinter Text widget and serializing Text back to XHTML."""

    @staticmethod
    def setup_default_tags(text_widget: tk.Text, font_family: str = "Segoe UI", font_size: int = 11):
        """Configures all base styling tags on a Text widget."""
        text_widget.tag_configure("normal", font=(font_family, font_size, "normal"))
        text_widget.tag_configure("bold", font=(font_family, font_size, "bold"))
        text_widget.tag_configure("italic", font=(font_family, font_size, "italic"))
        text_widget.tag_configure("bold_italic", font=(font_family, font_size, "bold italic"))
        text_widget.tag_configure("underline", underline=True)
        text_widget.tag_configure("strike", overstrike=True)

        # Headings
        text_widget.tag_configure("h1", font=(font_family, font_size + 9, "bold"), spacing1=12, spacing3=6)
        text_widget.tag_configure("h2", font=(font_family, font_size + 6, "bold"), spacing1=10, spacing3=4)
        text_widget.tag_configure("h3", font=(font_family, font_size + 3, "bold"), spacing1=8, spacing3=3)
        text_widget.tag_configure("h4", font=(font_family, font_size + 1, "bold"), spacing1=6, spacing3=2)

        # Code / Monospace
        text_widget.tag_configure("code", font=("Consolas", font_size, "normal"), background="#f2f2f2")
        text_widget.tag_configure("pre", font=("Consolas", font_size, "normal"), background="#f4f4f4", lmargin1=20, lmargin2=20)

        # Blockquote & Lists
        text_widget.tag_configure("blockquote", lmargin1=25, lmargin2=25, font=(font_family, font_size, "italic"), foreground="#555555")
        text_widget.tag_configure("bullet", lmargin1=20, lmargin2=35)
        text_widget.tag_configure("numbered", lmargin1=20, lmargin2=35)

        # Alignment
        text_widget.tag_configure("align_left", justify="left")
        text_widget.tag_configure("align_center", justify="center")
        text_widget.tag_configure("align_right", justify="right")

        # Links
        text_widget.tag_configure("link", foreground="#0b57d0", underline=True)

    @staticmethod
    def _ensure_newline(text_widget: tk.Text):
        content = text_widget.get("1.0", "end-1c")
        if content and not content.endswith("\n"):
            text_widget.insert(tk.END, "\n")

    @classmethod
    def load_html_to_text(
        cls,
        text_widget: tk.Text,
        html_content: str,
        base_dir: str = "",
        on_link_click: Optional[Callable[[str], None]] = None,
    ):
        """
        Parses KeepNote XHTML string and inserts formatted content into Tkinter Text widget.
        """
        text_widget.delete("1.0", tk.END)
        # Store image references on widget to prevent garbage collection
        if not hasattr(text_widget, "_embedded_images"):
            text_widget._embedded_images = []
        text_widget._embedded_images.clear()

        # Link click tracking
        if not hasattr(text_widget, "_link_targets"):
            text_widget._link_targets = {}
        text_widget._link_targets.clear()

        if not html_content or not html_content.strip():
            return

        soup = bs4.BeautifulSoup(html_content, "html.parser")
        body = soup.find("body") or soup

        link_counter = 0

        def traverse(node, current_tags: List[str]):
            nonlocal link_counter

            if isinstance(node, bs4.NavigableString):
                text = str(node)
                if text:
                    text_widget.insert(tk.END, text, tuple(current_tags))
                return

            if not isinstance(node, bs4.Tag):
                return

            tag_name = node.name.lower()
            new_tags = list(current_tags)

            BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "li", "blockquote", "pre", "ul", "ol"}

            # Before entering block element, ensure on a new line
            if tag_name in BLOCK_TAGS:
                cls._ensure_newline(text_widget)

            # Style mapping
            if tag_name in ("b", "strong"):
                if "italic" in new_tags:
                    new_tags = [t for t in new_tags if t != "italic"]
                    new_tags.append("bold_italic")
                else:
                    new_tags.append("bold")
            elif tag_name in ("i", "em"):
                if "bold" in new_tags:
                    new_tags = [t for t in new_tags if t != "bold"]
                    new_tags.append("bold_italic")
                else:
                    new_tags.append("italic")
            elif tag_name == "u":
                new_tags.append("underline")
            elif tag_name in ("s", "strike", "del"):
                new_tags.append("strike")
            elif tag_name in ("h1", "h2", "h3", "h4"):
                new_tags.append(tag_name)
            elif tag_name == "code":
                new_tags.append("code")
            elif tag_name == "pre":
                new_tags.append("pre")
            elif tag_name == "blockquote":
                new_tags.append("blockquote")

            # Inline CSS styles (color, background-color)
            style_str = node.get("style", "")
            if style_str:
                for rule in style_str.split(";"):
                    if ":" in rule:
                        prop, val = rule.split(":", 1)
                        prop = prop.strip().lower()
                        val = val.strip().lower()
                        if prop == "color" and (val.startswith("#") or val in ("red", "blue", "green", "black", "gray")):
                            tag_id = f"fg_{val}"
                            text_widget.tag_configure(tag_id, foreground=val)
                            new_tags.append(tag_id)
                        elif prop in ("background-color", "background") and (val.startswith("#") or val in ("yellow", "pink", "cyan", "lightgray")):
                            tag_id = f"bg_{val}"
                            text_widget.tag_configure(tag_id, background=val)
                            new_tags.append(tag_id)
                        elif prop == "text-align":
                            if val in ("center", "right", "left"):
                                new_tags.append(f"align_{val}")

            # Legacy <font color="..."> tag
            if tag_name == "font" and node.get("color"):
                color = node.get("color")
                tag_id = f"fg_{color}"
                text_widget.tag_configure(tag_id, foreground=color)
                new_tags.append(tag_id)

            # Anchor Links <a href="...">
            if tag_name == "a" and node.get("href"):
                link_counter += 1
                link_tag = f"link_{link_counter}"
                href = node.get("href")
                text_widget._link_targets[link_tag] = href

                text_widget.tag_configure(link_tag, foreground="#0b57d0", underline=True)
                new_tags.extend(["link", link_tag])

                if on_link_click:
                    text_widget.tag_bind(link_tag, "<Button-1>", lambda e, h=href: on_link_click(h))
                    text_widget.tag_bind(link_tag, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
                    text_widget.tag_bind(link_tag, "<Leave>", lambda e: text_widget.config(cursor="xterm"))

            # Line breaks
            if tag_name == "br":
                text_widget.insert(tk.END, "\n")
                return

            # Horizontal Rule
            if tag_name == "hr":
                text_widget.insert(tk.END, "\n" + "—" * 60 + "\n", ("strike",))
                return

            # Images <img src="...">
            if tag_name == "img":
                src = node.get("src", "")
                if src:
                    img_path = os.path.join(base_dir, src) if base_dir else src
                    if os.path.exists(img_path):
                        try:
                            pil_img = Image.open(img_path)
                            # Resize if huge
                            max_w, max_h = 750, 600
                            if pil_img.width > max_w or pil_img.height > max_h:
                                pil_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                            tk_img = ImageTk.PhotoImage(pil_img)
                            text_widget._embedded_images.append((tk_img, src))
                            text_widget.image_create(tk.END, image=tk_img)
                            text_widget.insert(tk.END, "\n")
                        except Exception:
                            text_widget.insert(tk.END, f"[Image: {src}]\n")
                    else:
                        text_widget.insert(tk.END, f"[Image: {src}]\n")
                return

            # Handle list items
            if tag_name == "li":
                parent_tag = node.parent.name.lower() if node.parent else ""
                bullet_char = "• " if parent_tag != "ol" else "1. "
                tag_to_apply = "bullet" if parent_tag != "ol" else "numbered"
                # Don't add bullet if styled none
                if "list-style-type: none" not in style_str:
                    text_widget.insert(tk.END, bullet_char, (tag_to_apply,))

            # Recurse children
            for child in node.children:
                traverse(child, new_tags)

            # Block level elements end with newline
            if tag_name in BLOCK_TAGS and tag_name not in ("ul", "ol"):
                cls._ensure_newline(text_widget)

        for child in body.children:
            traverse(child, [])

        # Clean trailing extra blank lines, leave just one
        full_text = text_widget.get("1.0", tk.END)
        if full_text.endswith("\n\n"):
            text_widget.delete("end-2c", "end-1c")

    @classmethod
    def save_text_to_html(cls, text_widget: tk.Text, title: str = "Note") -> str:
        """
        Serializes formatted content in Tkinter Text widget back to clean KeepNote XHTML.
        """
        escaped_title = html.escape(title)
        html_out = [
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            "<head>",
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />',
            f"<title>{escaped_title}</title>",
            "</head><body>",
        ]

        # Read line by line from text widget
        end_idx = text_widget.index("end-1c")
        num_lines = int(end_idx.split(".")[0])

        link_targets = getattr(text_widget, "_link_targets", {})

        in_ul = False
        in_ol = False

        for line_no in range(1, num_lines + 1):
            line_start = f"{line_no}.0"
            line_end = f"{line_no}.end"
            line_text = text_widget.get(line_start, line_end)

            if not line_text:
                if in_ul:
                    html_out.append("</ul>")
                    in_ul = False
                if in_ol:
                    html_out.append("</ol>")
                    in_ol = False
                html_out.append("<br/>")
                continue

            # Check if line is a bullet or numbered list
            line_tags = text_widget.tag_names(line_start)
            is_bullet = "bullet" in line_tags or line_text.startswith("• ")
            is_numbered = "numbered" in line_tags or re.match(r"^\d+\.\s", line_text)
            is_h1 = "h1" in line_tags
            is_h2 = "h2" in line_tags
            is_h3 = "h3" in line_tags
            is_hr = line_text.strip().startswith("——")

            if is_hr:
                if in_ul:
                    html_out.append("</ul>")
                    in_ul = False
                if in_ol:
                    html_out.append("</ol>")
                    in_ol = False
                html_out.append("<hr/>")
                continue

            if is_bullet:
                if not in_ul:
                    if in_ol:
                        html_out.append("</ol>")
                        in_ol = False
                    html_out.append("<ul>")
                    in_ul = True
            elif is_numbered:
                if not in_ol:
                    if in_ul:
                        html_out.append("</ul>")
                        in_ul = False
                    html_out.append("<ol>")
                    in_ol = True
            else:
                if in_ul:
                    html_out.append("</ul>")
                    in_ul = False
                if in_ol:
                    html_out.append("</ol>")
                    in_ol = False

            # Strip leading bullet/number prefix for the li content if needed
            content_start_col = 0
            if is_bullet and line_text.startswith("• "):
                content_start_col = 2
            elif is_numbered:
                m = re.match(r"^(\d+\.\s)", line_text)
                if m:
                    content_start_col = len(m.group(1))

            # Build line fragments by inspecting character tags
            fragments: List[Tuple[str, List[str]]] = []
            curr_text = ""
            curr_tags = None

            for col in range(content_start_col, len(line_text)):
                char_idx = f"{line_no}.{col}"
                tags = sorted([t for t in text_widget.tag_names(char_idx) if t not in ("bullet", "numbered")])
                char = line_text[col]

                if curr_tags is None:
                    curr_tags = tags
                    curr_text = char
                elif tags == curr_tags:
                    curr_text += char
                else:
                    fragments.append((curr_text, curr_tags))
                    curr_tags = tags
                    curr_text = char

            if curr_text:
                fragments.append((curr_text, curr_tags or []))

            # Convert fragments to HTML snippet
            line_html_parts = []
            for frag_text, tags in fragments:
                part = html.escape(frag_text)
                # Apply inline tags
                if "bold" in tags or "bold_italic" in tags:
                    part = f"<b>{part}</b>"
                if "italic" in tags or "bold_italic" in tags:
                    part = f"<i>{part}</i>"
                if "underline" in tags:
                    part = f"<u>{part}</u>"
                if "strike" in tags:
                    part = f"<s>{part}</s>"
                if "code" in tags:
                    part = f"<code>{part}</code>"

                # Color styles
                for t in tags:
                    if t.startswith("fg_"):
                        c = t[3:]
                        part = f'<span style="color: {c}">{part}</span>'
                    elif t.startswith("bg_"):
                        c = t[3:]
                        part = f'<span style="background-color: {c}">{part}</span>'
                    elif t.startswith("link_") and t in link_targets:
                        href = link_targets[t]
                        part = f'<a href="{html.escape(href)}">{part}</a>'

                line_html_parts.append(part)

            line_inner = "".join(line_html_parts)

            # Wrap in line block tag
            if is_bullet or is_numbered:
                html_out.append(f"<li>{line_inner}</li>")
            elif is_h1:
                html_out.append(f"<h1>{line_inner}</h1>")
            elif is_h2:
                html_out.append(f"<h2>{line_inner}</h2>")
            elif is_h3:
                html_out.append(f"<h3>{line_inner}</h3>")
            else:
                html_out.append(f"<p>{line_inner}</p>")

        if in_ul:
            html_out.append("</ul>")
        if in_ol:
            html_out.append("</ol>")

        html_out.append("</body></html>")
        return "\n".join(html_out)
