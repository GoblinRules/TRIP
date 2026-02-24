"""
TRIP — Background IP monitor with callback-based change notification.
"""

from __future__ import annotations

import threading
import time
import requests
from .constants import IP_API_URL


class IPMonitor:
    """Polls the public IP at a configurable interval and fires callbacks on change."""

    def __init__(self, config, logger, on_change=None, on_check=None):
        """
        Args:
            config:    ConfigManager instance
            logger:    LoggingManager instance
            on_change: callback(old_ip, new_ip) — called on IP change
            on_check:  callback(ip) — called after every successful check
        """
        self._config = config
        self._logger = logger
        self._on_change = on_change
        self._on_check = on_check
        self._current_ip: str | None = None
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._last_manual = 0.0
        self._thread: threading.Thread | None = None

    @property
    def current_ip(self) -> str | None:
        return self._current_ip

    # ── Lifecycle ────────────────────────────────────────────────────────

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ip-monitor")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._wake_event.set()

    def wake(self) -> None:
        """Interrupt the sleep to re-check immediately (e.g. after settings change)."""
        self._wake_event.set()

    # ── Manual recheck (debounced) ───────────────────────────────────────

    def recheck(self) -> None:
        now = time.time()
        if now - self._last_manual < 2:
            return
        self._last_manual = now
        self._do_check(manual=True)

    # ── Internal loop ────────────────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._do_check(manual=False)
            interval = self._config.check_interval
            # Wait for interval OR until woken
            self._wake_event.wait(timeout=interval)
            self._wake_event.clear()

    def _do_check(self, manual: bool) -> None:
        ip = self._fetch_ip()
        if ip is None:
            return
        old = self._current_ip
        changed = ip != old and old is not None
        self._current_ip = ip

        # Log the check
        if self._config.enable_logging:
            self._logger.log_ip(
                target_ip=self._config.target_ip,
                detected_ip=ip,
                changed=changed,
                manual=manual,
            )

        # Fire callbacks
        if changed and self._on_change:
            try:
                self._on_change(old, ip)
            except Exception as e:
                self._logger.log_error(e)
        if self._on_check:
            try:
                self._on_check(ip)
            except Exception as e:
                self._logger.log_error(e)

    def _fetch_ip(self) -> str | None:
        try:
            r = requests.get(IP_API_URL, timeout=8)
            r.raise_for_status()
            data = r.json()
            return data.get("ip") or data.get("query")
        except Exception as e:
            self._logger.log_error(e)
            return None
