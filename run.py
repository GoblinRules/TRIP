"""
TRIP (Tray IP) — launcher script.

Run this file directly:  python run.py
"""

import ctypes
import sys

# Tell Windows this process is DPI-aware so tray icons render
# at the correct size on high-DPI displays.
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # Per-monitor V2
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()     # Fallback
        except Exception:
            pass

from src.main import main

if __name__ == "__main__":
    main()
