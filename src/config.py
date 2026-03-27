"""
TRIP — Thread-safe configuration manager.

Wraps configparser with locking, defaults, and auto-migration
from the old ippy-tray-app config format.
"""

from __future__ import annotations

import configparser
import os
import threading
from .constants import CONFIG_PATH, DEFAULT_SETTINGS


class ConfigManager:
    """Thread-safe INI configuration backed by a file on disk."""

    SECTION = "Settings"

    def __init__(self, path: str = CONFIG_PATH):
        self._path = path
        self._lock = threading.Lock()
        self._parser = configparser.ConfigParser()
        self.first_run = False
        self._load()

    # ── public API ───────────────────────────────────────────────────────

    def get(self, key: str, fallback: str | None = None) -> str:
        with self._lock:
            return self._parser.get(self.SECTION, key, fallback=fallback or DEFAULT_SETTINGS.get(key, ""))

    def get_bool(self, key: str, fallback: bool = True) -> bool:
        with self._lock:
            return self._parser.getboolean(self.SECTION, key, fallback=fallback)

    def get_int(self, key: str, fallback: int = 0) -> int:
        with self._lock:
            try:
                return self._parser.getint(self.SECTION, key)
            except (ValueError, configparser.NoOptionError):
                return fallback

    def get_float(self, key: str, fallback: float = 0.0) -> float:
        with self._lock:
            try:
                return self._parser.getfloat(self.SECTION, key)
            except (ValueError, configparser.NoOptionError):
                return fallback

    def set(self, key: str, value: str) -> None:
        with self._lock:
            if not self._parser.has_section(self.SECTION):
                self._parser.add_section(self.SECTION)
            self._parser.set(self.SECTION, key, value)

    def save(self) -> None:
        with self._lock:
            with open(self._path, "w", encoding="utf-8") as fh:
                self._parser.write(fh)

    def reload(self) -> None:
        self._load()

    # ── Convenience properties ───────────────────────────────────────────

    @property
    def target_ip(self) -> str:
        return self.get("target_ip")

    @property
    def check_interval(self) -> int:
        val = self.get_int("check_interval", fallback=60)
        return max(5, min(3600, val))    # clamp 5s – 1h

    @property
    def notify_on_change(self) -> bool:
        return self.get_bool("notify_on_change")

    @property
    def enable_logging(self) -> bool:
        return self.get_bool("enable_logging")

    @property
    def always_on_screen(self) -> bool:
        return self.get_bool("always_on_screen")

    @property
    def log_retention_days(self) -> int:
        val = self.get_int("log_retention_days", fallback=60)
        return max(1, min(365, val))

    @property
    def flash_on_change(self) -> bool:
        return self.get_bool("flash_on_change", fallback=False)

    @property
    def close_browsers_on_change(self) -> bool:
        return self.get_bool("close_browsers_on_change", fallback=False)

    @property
    def restart_on_change(self) -> bool:
        return self.get_bool("restart_on_change", fallback=False)

    @property
    def window_alpha(self) -> float:
        return self.get_float("window_alpha", fallback=0.85)

    @property
    def window_x(self) -> int:
        return self.get_int("window_x", fallback=100)

    @property
    def window_y(self) -> int:
        return self.get_int("window_y", fallback=100)

    # ── internal ─────────────────────────────────────────────────────────

    def _load(self) -> None:
        with self._lock:
            if not os.path.exists(self._path):
                self._write_defaults()
                self.first_run = True
            else:
                self._parser.read(self._path, encoding="utf-8")
                self._migrate()
                self.first_run = False

    def _write_defaults(self) -> None:
        self._parser[self.SECTION] = dict(DEFAULT_SETTINGS)
        with open(self._path, "w", encoding="utf-8") as fh:
            self._parser.write(fh)

    def _migrate(self) -> None:
        """Add any missing keys from DEFAULT_SETTINGS (forward compat)."""
        changed = False
        if not self._parser.has_section(self.SECTION):
            self._parser.add_section(self.SECTION)
            changed = True
        for key, default in DEFAULT_SETTINGS.items():
            if not self._parser.has_option(self.SECTION, key):
                self._parser.set(self.SECTION, key, default)
                changed = True
        # Migrate old "checks per minute" to "seconds" if the value looks like CPM
        try:
            interval = self._parser.getint(self.SECTION, "check_interval")
            if interval <= 45:  # Old CPM-style value
                seconds = max(5, int(60 / max(1, interval)))
                self._parser.set(self.SECTION, "check_interval", str(seconds))
                changed = True
        except (ValueError, configparser.NoOptionError):
            pass
        if changed:
            with open(self._path, "w", encoding="utf-8") as fh:
                self._parser.write(fh)
