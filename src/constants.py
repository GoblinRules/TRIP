r"""
TRIP (Tray IP) -- Application constants and path resolution.

Supports two modes:
  - Portable: a `portable.flag` file exists next to the executable/script.
    Data is stored alongside the exe.
  - Installed: data stored in %LOCALAPPDATA%\TRIP.
"""

import os
import sys

# ── App metadata ─────────────────────────────────────────────────────────────
APP_NAME = "TRIP"
APP_DISPLAY_NAME = "TRIP — Tray IP"
APP_VERSION = "2.0.0"
IP_API_URL = "https://ipinfo.io/json"
DEFAULT_IP = "0.0.0.0"

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "target_ip": DEFAULT_IP,
    "check_interval": "60",          # seconds between checks
    "notify_on_change": "yes",
    "enable_logging": "yes",
    "always_on_screen": "yes",
    "window_alpha": "0.85",
    "window_x": "100",
    "window_y": "100",
    "log_retention_days": "60",      # auto-purge threshold
}

# ── Path resolution ──────────────────────────────────────────────────────────

def _is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def _bundle_dir() -> str:
    """Directory where bundled data files live (sys._MEIPASS for one-file)."""
    if _is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _exe_dir() -> str:
    """Directory containing the exe (frozen) or the src/ package (dev)."""
    if _is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _is_portable() -> bool:
    """Portable mode if `portable.flag` exists next to the exe / src dir."""
    return os.path.isfile(os.path.join(_exe_dir(), "portable.flag"))


def _data_dir() -> str:
    """Resolve the writable data directory (config, logs)."""
    if _is_portable() or not _is_frozen():
        return _exe_dir()
    return os.path.join(os.environ.get("LOCALAPPDATA", _exe_dir()), APP_NAME)


# ── Concrete paths ───────────────────────────────────────────────────────────
BASE_DIR = _exe_dir()
DATA_DIR = _data_dir()
# Assets live inside the PyInstaller bundle (read-only) in frozen mode
ASSETS_DIR = os.path.join(_bundle_dir(), "src", "assets") if _is_frozen() else os.path.join(BASE_DIR, "assets")
LOG_DIR = os.path.join(DATA_DIR, "logs")
CONFIG_PATH = os.path.join(DATA_DIR, "config.ini")

# Icon paths — resolved at import time; modules should reference these.
ICON_DEFAULT = os.path.join(ASSETS_DIR, "trip_icon.ico")
ICON_GREEN = os.path.join(ASSETS_DIR, "trip_icon_green.ico")
ICON_RED = os.path.join(ASSETS_DIR, "trip_icon_red.ico")
ICON_PNG = os.path.join(ASSETS_DIR, "trip_icon.png")

# Per-size PNGs for crisp tray rendering (avoids ICO extraction issues)
ICON_DEFAULT_48 = os.path.join(ASSETS_DIR, "trip_icon_48.png")
ICON_GREEN_48 = os.path.join(ASSETS_DIR, "trip_icon_green_48.png")
ICON_RED_48 = os.path.join(ASSETS_DIR, "trip_icon_red_48.png")

LOG_FILE = os.path.join(LOG_DIR, "ip_changes.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

# Ensure directories exist
for _d in (DATA_DIR, ASSETS_DIR, LOG_DIR):
    os.makedirs(_d, exist_ok=True)
