## TRIP v2.2.0 — Reliability Update

### Bug Fixes
- 🌐 **Fixed "stuck on checking..."** — added 6 fallback IP providers so the app works even if one service is blocked or rate-limited
- 🟡 **Error state on floating window** — shows yellow "UNAVAILABLE" instead of staying stuck on "checking..." forever

### IP Providers (tried in order)
1. api.ipify.org
2. ipinfo.io
3. httpbin.org
4. ifconfig.me
5. icanhazip.com
6. api.my-ip.io

### Downloads
| File | Description |
|------|-------------|
| TRIP.exe | Portable — run from any folder |
| TRIP_Setup.exe | Full installer with Start Menu + startup shortcuts |
