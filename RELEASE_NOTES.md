## TRIP v2.3.0 — AV Hardening

### Improvements
- 🛡️ **Disabled UPX compression** — removes the most common trigger for Windows Defender false positives
- 📋 **Embedded version info resource** — EXE now contains full metadata (publisher, description, copyright) visible in Properties → Details
- 🔒 **Reduced AV heuristic score** — combination of no-UPX + version info + module exclusions makes the binary look legitimate

### Bug Fixes
- 🌐 **Fixed "stuck on checking..."** — added 6 fallback IP providers so the app works even if one service is blocked or rate-limited
- 🟡 **Error state on floating window** — shows yellow "UNAVAILABLE" instead of staying stuck on "checking..." forever

### Downloads
| File | Description |
|------|-------------|
| TRIP.exe | Portable — run from any folder |
| TRIP_Setup.exe | Full installer with Start Menu + startup shortcuts |
