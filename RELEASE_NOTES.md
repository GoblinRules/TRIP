## TRIP v2.1.0 — Patch Release

### Bug Fixes
- 🔧 **Fixed tray Recheck IP** — recheck now properly wakes the monitor thread instead of calling the check from the wrong thread
- 🔧 **Fixed purge dialog freeze** — replaced modal Toplevel dialog with borderless popup panel (no `grab_set`, no modal behavior)
- 🔧 **Fixed settings X button** — now cleanly closes the settings window instead of triggering the close-app prompt
- 🔧 **Python 3.9+ compatibility** — added `from __future__ import annotations` to all modules

### Improvements
- ⚡ IP monitor runs all checks on its dedicated background thread
- ⚡ Purge operations run in a background thread (no UI freezes)
- ⚡ Styled confirmation dialog for purge actions with hover effects

### Downloads
| File | Description |
|------|-------------|
| TRIP.exe | Portable — run from any folder |
| TRIP_Setup.exe | Full installer with Start Menu + startup shortcuts |

### Requirements
- Windows 10/11 (64-bit)
- No additional dependencies needed — everything is bundled
