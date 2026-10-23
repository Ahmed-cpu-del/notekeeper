"""
Application configuration and preferences for NoteKeeper.
Stores persistent settings in %APPDATA%/NoteKeeper/config.json.
"""

import os
import json

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NoteKeeper")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "last_notebook": "",
    "recent_notebooks": [],
    "autosave": True,
    "autosave_interval_ms": 10000,
    "window_width": 1100,
    "window_height": 720,
    "window_maximized": False,
    "show_tree": True,
    "show_list": True,
    "show_status": True,
    "default_font_family": "Segoe UI",
    "default_font_size": 11,
    "splitter_h_pos": 260,
    "splitter_v_pos": 180,
}


def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config.update(data)
        except Exception:
            pass
    return config


def save_config(config: dict):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass


class ConfigManager:
    """Manages application configuration, persisting to disk."""

    def __init__(self):
        self.config = load_config()

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def set(self, key: str, value):
        self.config[key] = value
        self.save()

    def get_recent_notebooks(self) -> list:
        recents = self.config.get("recent_notebooks", [])
        return [p for p in recents if os.path.isdir(p)]

    def add_recent_notebook(self, path: str):
        path = os.path.abspath(path)
        recents = self.get_recent_notebooks()
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        self.config["recent_notebooks"] = recents[:10]
        self.config["last_notebook"] = path
        self.save()

    def save(self):
        save_config(self.config)
