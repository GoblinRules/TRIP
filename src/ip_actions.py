"""
TRIP — IP change reaction actions (close browsers, restart PC).
"""

import subprocess


# Browser process names to kill
_BROWSER_PROCESSES = [
    "chrome.exe",
    "firefox.exe",
    "msedge.exe",
    "brave.exe",
    "opera.exe",
    "vivaldi.exe",
]


def close_all_browsers() -> None:
    """Forcefully terminate all known browser processes."""
    for proc in _BROWSER_PROCESSES:
        try:
            subprocess.run(
                ["taskkill", "/IM", proc, "/F"],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass  # Process may not be running — that's fine


def restart_pc(delay_seconds: int = 5) -> None:
    """Schedule a PC restart with a grace period.

    Args:
        delay_seconds: Seconds before the restart occurs (default 5).
    """
    try:
        subprocess.Popen(
            ["shutdown", "/r", "/t", str(delay_seconds)],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception:
        pass
