# NoteKeeper 📝

> A modern, lightweight hierarchical note-taking application inspired by **KeepNote**, redesigned from the ground up for Windows 11.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com/windows)
[![Compatibility](https://img.shields.io/badge/KeepNote-100%25%20Compatible-brightgreen.svg)](#bidirectional-keepnote-compatibility)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Overview

**NoteKeeper** brings back the beloved, distraction-free workflow of the classic **KeepNote** application, completely re-engineered in modern Python 3 with high-DPI scaling and native Windows 11 integration.

Say goodbye to legacy GTK2 deprecation crashes, font scaling issues, and update popups—NoteKeeper provides the exact same intuitive 3-pane layout and hierarchical structure while remaining **100% bidirectionally compatible** with your existing KeepNote notebooks.

---


## 🚀 Key Features

* **100% Bidirectional KeepNote Compatibility:**
  * Opens and saves native KeepNote directories seamlessly (`notebook.nbk`, `node.xml`, `page.html`).
  * Full support for internal note links (`nbk:///<node-uuid>`) and embedded images.
  * Your notes remain plain XHTML and XML files on your filesystem—no proprietary database locks.
* **Modern Windows 11 Experience:**
  * Native per-monitor High-DPI scaling (`shcore` aware) for ultra-sharp typography on 4K/retina displays.
  * Zero startup lag (< 0.2s launch time).
  * 100% self-contained—runs completely offline without requiring internet access.
* **Rich Text Formatting:**
  * Headings (Heading 1, 2, 3), Bold, Italic, Underline, Strikethrough.
  * Custom text colors and background highlighter colors.
  * Bulleted lists (`•`) and numbered lists (`1.`).
  * Horizontal dividers (`<hr/>`), timestamps, and embedded images (`PNG`, `JPG`, `GIF`, `WebP`).
* **Multi-Tab Document Viewer:**
  * Keep multiple notes open simultaneously in tabs.
* **Instant Global Search:**
  * Live search box on the toolbar scans note titles and full text across your entire notebook in milliseconds.
* **Windows Explorer & Notepad Integration:**
  * Right-click any note or folder to reveal it directly in Windows File Explorer or open its raw source in Notepad.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + S` | Save current note |
| `Ctrl + Shift + S` | Save all open notes |
| `Ctrl + N` | Create new note page |
| `Ctrl + Shift + N` | Create new folder |
| `Ctrl + O` | Open notebook directory |
| `Ctrl + Shift + O` | Create brand new notebook |
| `Ctrl + F` | Toggle Find & Replace bar |
| `Ctrl + B` | Toggle **Bold** |
| `Ctrl + I` | Toggle *Italic* |
| `Ctrl + U` | Toggle <u>Underline</u> |
| `Ctrl + K` | Insert Hyperlink |
| `Ctrl + W` | Close active note tab |
| `F2` | Rename selected item |
| `Del` | Delete selected item |
| `F5` | Refresh notebook tree |

---

## 🛠️ Installation & Getting Started

### Prerequisites
* Windows 10 / 11
* Python 3.9+ (Python 3.10, 3.11, 3.12, 3.13, 3.14 fully supported)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/Ahmed-cpu-del/notekeeper.git
   cd notekeeper
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch NoteKeeper:
   ```bash
   run.bat
   ```
   *Or with Python directly:*
   ```bash
   python notekeeper/main.py
   ```

---

## 📁 KeepNote Compatibility Guarantee

NoteKeeper can be used as a drop-in replacement for KeepNote 0.7.x. You can open existing notebooks created by KeepNote without converting or exporting:
* Format Version 6 notebooks are natively read and written.
* Open your notes in NoteKeeper or KeepNote interchangeably at any time.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Inspired by [KeepNote](http://keepnote.org/) by Matt Rasmussen.
