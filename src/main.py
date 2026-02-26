"""
TRIP (Tray IP) — Main entry point.

Wires together all components: config, logger, tray, monitor, UI.
"""

from __future__ import annotations

import atexit
import queue
import signal
import sys
import threading
import tkinter as tk
from tkinter import messagebox

from .config import ConfigManager
from .constants import APP_DISPLAY_NAME
from .ip_monitor import IPMonitor
from .logging_manager import LoggingManager
from .notifications import notify_ip_change
from .ui.floating_window import FloatingWindow
from .ui.settings_window import SettingsWindow
from .ui.tray import TrayManager


class TripApp:
    """Application orchestrator — owns all components and the Tk mainloop."""

    def __init__(self):
        self._config = ConfigManager()
        self._logger = LoggingManager(retention_days=self._config.log_retention_days)

        # Tk root (hidden)
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.title(APP_DISPLAY_NAME)

        # Handle WM_DELETE_WINDOW on root (shouldn't normally fire since it's withdrawn)
        self._root.protocol("WM_DELETE_WINDOW", self._on_root_close)

        # GUI task queue (thread → main thread bridge)
        self._gui_queue: queue.Queue = queue.Queue()

        # Sub-components (created later)
        self._float_win: FloatingWindow | None = None
        self._settings_win: SettingsWindow | None = None
        self._tray: TrayManager | None = None
        self._monitor: IPMonitor | None = None
        self._overlay_visible = False
        self._shutting_down = False

    # ── Bootstrap ────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start everything and enter the mainloop."""
        # Tray
        self._tray = TrayManager(
            tk_root=self._root,
            on_settings=lambda: self._enqueue(self._show_settings),
            on_toggle_overlay=lambda: self._enqueue(self._toggle_overlay),
            on_recheck=lambda: self._monitor.recheck() if self._monitor else None,
            on_exit=lambda: self._enqueue(self._shutdown),
        )
        self._tray.start()

        # IP monitor
        self._monitor = IPMonitor(
            config=self._config,
            logger=self._logger,
            on_change=self._on_ip_change,
            on_check=lambda ip: self._enqueue(self._on_ip_checked, ip),
        )
        self._monitor.start()

        # Initial overlay
        if self._config.first_run or self._config.always_on_screen:
            self._root.after(500, self._toggle_overlay)

        # First-run: open settings
        if self._config.first_run:
            self._root.after(600, self._show_settings)

        # Process GUI queue
        self._process_queue()

        # Clean exit hooks
        atexit.register(self._cleanup)
        signal.signal(signal.SIGINT, lambda *_: self._shutdown())
        signal.signal(signal.SIGTERM, lambda *_: self._shutdown())

        self._root.mainloop()

    # ── GUI queue ────────────────────────────────────────────────────────

    def _enqueue(self, fn, *args) -> None:
        """Schedule a callable on the main (Tk) thread."""
        self._gui_queue.put((fn, args))

    def _process_queue(self) -> None:
        while not self._gui_queue.empty():
            fn, args = self._gui_queue.get_nowait()
            try:
                fn(*args)
            except Exception as e:
                self._logger.log_error(e)
        if not self._shutting_down:
            self._root.after(80, self._process_queue)

    # ── Callbacks ────────────────────────────────────────────────────────

    def _on_ip_change(self, old_ip: str, new_ip: str) -> None:
        """Called from monitor thread on IP change."""
        if self._config.notify_on_change:
            notify_ip_change(old_ip, new_ip)

    def _on_ip_checked(self, ip: str) -> None:
        """Called on main thread after every check."""
        target = self._config.target_ip
        # Update overlay
        if self._float_win and self._float_win.winfo_exists():
            self._float_win.update_ip(ip, target)
        # Update tray icon
        if self._tray:
            self._tray.set_status(ip == target)

    # ── Overlay ──────────────────────────────────────────────────────────

    def _toggle_overlay(self) -> None:
        if self._float_win and self._float_win.winfo_exists():
            if self._float_win.state() != "withdrawn":
                self._float_win.withdraw()
                self._overlay_visible = False
            else:
                self._float_win.deiconify()
                self._overlay_visible = True
        else:
            self._float_win = FloatingWindow(self._root, self._config)
            self._overlay_visible = True
            # Show current IP immediately if known
            if self._monitor and self._monitor.current_ip:
                self._float_win.update_ip(self._monitor.current_ip, self._config.target_ip)
        if self._tray:
            self._tray.overlay_visible = self._overlay_visible

    # ── Settings ─────────────────────────────────────────────────────────

    def _show_settings(self) -> None:
        if self._settings_win is None or not self._settings_win.is_open():
            self._settings_win = SettingsWindow(
                self._root,
                self._config,
                self._logger,
                on_save=self._on_settings_saved,
                on_close_app=self._ask_close_or_minimise,
            )
        self._settings_win.show()

    def _on_settings_saved(self) -> None:
        """React to settings changes."""
        # Wake the monitor to use the new interval / target
        if self._monitor:
            self._monitor.wake()
        # Update tray icon
        if self._tray and self._monitor and self._monitor.current_ip:
            self._tray.set_status(self._monitor.current_ip == self._config.target_ip)
        # Handle overlay toggle
        should_show = self._config.always_on_screen
        if should_show and not self._overlay_visible:
            self._toggle_overlay()
        elif not should_show and self._overlay_visible:
            self._toggle_overlay()

    # ── Close prompt (X button) ──────────────────────────────────────────

    def _on_root_close(self) -> None:
        """Prompt the user when they try to close — minimise to tray or quit."""
        self._ask_close_or_minimise()

    def _ask_close_or_minimise(self) -> None:
        """Show a dialog: Minimise to Tray / Close App / Cancel."""
        # Create a custom styled dialog
        dlg = tk.Toplevel(self._root)
        dlg.title("Close TRIP?")
        dlg.geometry("380x180")
        dlg.resizable(False, False)
        dlg.configure(bg="#16162a")
        dlg.transient(self._root)
        dlg.lift()
        dlg.focus_force()

        # Center on screen
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - 190
        y = (dlg.winfo_screenheight() // 2) - 90
        dlg.geometry(f"+{x}+{y}")

        tk.Label(dlg, text="What would you like to do?",
                font=("Segoe UI Semibold", 12),
                bg="#16162a", fg="#e2e8f0").pack(pady=(20, 16))

        btn_frame = tk.Frame(dlg, bg="#16162a")
        btn_frame.pack(pady=(0, 10))

        def _make_btn(parent, text, bg, fg, command):
            btn = tk.Label(parent, text=f"  {text}  ", font=("Segoe UI Semibold", 10),
                          bg=bg, fg=fg, cursor="hand2", padx=14, pady=8)
            btn.pack(side="left", padx=6)
            btn.bind("<Button-1>", lambda e: self._root.after(10, command))
            hover_bg = "#818cf8" if bg == "#6366f1" else "#2a2a52"
            btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
            btn.bind("<Leave>", lambda e: btn.config(bg=bg))
            return btn

        def minimise():
            dlg.destroy()
            # Hide overlay and settings, keep running in tray
            if self._float_win and self._float_win.winfo_exists():
                self._float_win.withdraw()
                self._overlay_visible = False
                if self._tray:
                    self._tray.overlay_visible = False
            if self._settings_win and self._settings_win.is_open():
                self._settings_win.destroy()

        def close_app():
            dlg.destroy()
            self._shutdown()

        def cancel():
            dlg.destroy()

        _make_btn(btn_frame, "Minimise to Tray", "#6366f1", "#ffffff", minimise)
        _make_btn(btn_frame, "Close App", "#ef4444", "#ffffff", close_app)
        _make_btn(btn_frame, "Cancel", "#1e1e3a", "#94a3b8", cancel)

        dlg.protocol("WM_DELETE_WINDOW", cancel)

    # ── Shutdown ─────────────────────────────────────────────────────────

    def _shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._cleanup()
        try:
            self._root.quit()
        except Exception:
            pass

    def _cleanup(self) -> None:
        if self._monitor:
            self._monitor.stop()
        if self._settings_win:
            try:
                self._settings_win.destroy()
            except Exception:
                pass
        if self._float_win:
            try:
                self._float_win.destroy()
            except Exception:
                pass
        if self._tray:
            self._tray.stop()


def main():
    app = TripApp()
    app.run()


if __name__ == "__main__":
    main()
