"""
TRIP — Windows toast notifications via winotify.
"""

import os
from .constants import ICON_PNG, APP_DISPLAY_NAME


def notify_ip_change(old_ip: str, new_ip: str) -> None:
    """Show a Windows toast notification for an IP change."""
    try:
        from winotify import Notification
        toast = Notification(
            app_id=APP_DISPLAY_NAME,
            title="IP Address Changed",
            msg=f"{old_ip}  ➔  {new_ip}",
            duration="short",
        )
        if os.path.isfile(ICON_PNG):
            toast.set_audio(None, loop=False)
            toast.icon = ICON_PNG
        toast.show()
    except ImportError:
        # winotify not installed — fall back to silent
        pass
    except Exception:
        pass  # Notifications are non-critical
