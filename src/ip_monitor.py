"""
TRIP — Background IP monitor with callback-based change notification.
"""

from __future__ import annotations

import threading
import time
import requests


# Multiple IP lookup services — if one fails, try the next.
_IP_PROVIDERS = [
    ("https://api.ipify.org?format=json", "ip"),
    ("https://ipinfo.io/json", "ip"),
    ("https://httpbin.org/ip", "origin"),
    ("https://ifconfig.me/ip", None),        # plain text
    ("https://icanhazip.com", None),          # plain text
    ("https://api.my-ip.io/v2/ip.json", "ip"),
]


class IPMonitor:
    """Polls the public IP at a configurable interval and fires callbacks on change."""

    def __init__(self, config, logger, on_change=None, on_check=None, on_error=None):
        """
        Args:
            config:    ConfigManager instance
            logger:    LoggingManager instance
            on_change: callback(old_ip, new_ip) — called on IP change
            on_check:  callback(ip) — called after every successful check
            on_error:  callback() — called when all providers fail
        """
        self._config = config
        self._logger = logger
        self._on_change = on_change
        self._on_check = on_check
        self._on_error = on_error
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
        """Trigger an immediate recheck by waking the monitor thread."""
        now = time.time()
        if now - self._last_manual < 2:
            return
        self._last_manual = now
        self._force_check = True
        self._wake_event.set()

    # ── Internal loop ────────────────────────────────────────────────────

    def _loop(self) -> None:
        self._force_check = False
        while not self._stop_event.is_set():
            self._do_check(manual=self._force_check)
            self._force_check = False
            interval = self._config.check_interval
            self._wake_event.wait(timeout=interval)
            self._wake_event.clear()

    def _do_check(self, manual: bool) -> None:
        ip = self._fetch_ip()
        if ip is None:
            if self._on_error:
                try:
                    self._on_error()
                except Exception:
                    pass
            return
        old = self._current_ip
        changed = ip != old and old is not None
        self._current_ip = ip

        if self._config.enable_logging:
            self._logger.log_ip(
                target_ip=self._config.target_ip,
                detected_ip=ip,
                changed=changed,
                manual=manual,
            )

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
        """Try multiple IP lookup services, return first success."""
        for url, json_key in _IP_PROVIDERS:
            try:
                r = requests.get(url, timeout=6, headers={"User-Agent": "TRIP/2.1"})
                r.raise_for_status()
                if json_key:
                    ip = r.json().get(json_key, "").strip()
                else:
                    ip = r.text.strip()
                if ip and len(ip) <= 45:  # sanity check (max IPv6 length)
                    return ip
            except Exception:
                continue
        self._logger.log_error(Exception("All IP providers failed"))
        return None
