# 🛰️ TRIP — Tray IP

A lightweight Windows system tray utility that monitors your public IP address, logs changes, and notifies you when it changes.

---

## ✨ Features

- **IP Monitoring** — Tracks your public IP and compares it to a configurable target
- **Toast Notifications** — Windows native alerts when your IP changes
- **Floating Overlay** — Always-on-top, draggable IP status window with colour-coded state
- **Rich Log Viewer** — Paginated, searchable, sortable log table with CSV export
- **Auto-Purge** — Automatically removes log entries older than a configurable threshold (default: 60 days)
- **Portable & Installer** — Run standalone or install with Start Menu + startup shortcuts
- **Lightweight** — Runs silently from the system tray

---

## 📦 Download

| Build | Description |
|-------|-------------|
| `TRIP.exe` | Portable — no install needed, runs from any folder |
| `TRIP_Setup.exe` | Full installer — installs to `%LOCALAPPDATA%\TRIP` with shortcuts |

---

## ⚙️ Configuration

Settings are stored in `config.ini` (auto-created on first run):

```ini
[Settings]
target_ip = 0.0.0.0
check_interval = 60
notify_on_change = yes
enable_logging = yes
always_on_screen = yes
window_alpha = 0.85
window_x = 100
window_y = 100
log_retention_days = 60
```

| Setting | Description | Range |
|---------|-------------|-------|
| `target_ip` | IP address to compare against | Any valid IP |
| `check_interval` | Seconds between checks | 5–3600 |
| `notify_on_change` | Show toast on IP change | yes/no |
| `enable_logging` | Write checks to log file | yes/no |
| `always_on_screen` | Show floating overlay on launch | yes/no |
| `log_retention_days` | Auto-purge logs older than N days | 1–365 |

---

## 🖥️ Usage

- Right-click the tray icon for:
  - **Settings** — configure target IP, interval, logging, and more
  - **Show/Hide IP Window** — toggle the floating overlay
  - **Recheck IP** — manually trigger a check now
  - **Exit** — close the application

---

## 🏗️ Building from Source

### Requirements
- Python 3.12+
- PyInstaller (`pip install pyinstaller`)
- Inno Setup 6 *(optional, for installer)*

### Steps

```powershell
# Install dependencies
pip install -r requirements.txt

# Run from source
python run.py

# Build portable exe + installer
powershell -File build.ps1
```

---

## 📁 Project Structure

```
Trip - Tray IP/
├── run.py                    # Entry point
├── requirements.txt
├── trip.spec                 # PyInstaller config
├── installer.iss             # Inno Setup config
├── build.ps1                 # Build script
├── src/
│   ├── main.py               # App orchestrator
│   ├── constants.py           # Paths & metadata
│   ├── config.py              # Thread-safe config
│   ├── ip_monitor.py          # Background IP poller
│   ├── logging_manager.py     # CSV logger + auto-purge
│   ├── notifications.py       # Windows toast wrapper
│   └── ui/
│       ├── floating_window.py # Draggable overlay
│       ├── settings_window.py # Settings dialog
│       └── tray.py            # System tray manager
└── assets/
    └── icon_pack/             # Source icons
```

---

## ⚠️ Disclaimer

This software is provided **as-is** with no guarantees of accuracy, uptime, or fitness for any particular purpose. TRIP relies on third-party IP lookup services (`ipinfo.io`) which may be rate-limited, unavailable, or return inaccurate results. **Do not** rely on this tool for security-critical monitoring. The authors are not responsible for any damages, data loss, or issues arising from the use of this software. Use at your own risk.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## 👤 Maintainer

**GoblinRules** — [GitHub](https://github.com/GoblinRules)
