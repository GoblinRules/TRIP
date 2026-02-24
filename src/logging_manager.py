"""
TRIP — IP change logger with auto-purge and paginated reading.

Log format (pipe-delimited CSV):
  Date|Time|TargetIP|DetectedIP|Changed|Manual
"""

import csv
import datetime
import os
import threading
import traceback
from .constants import LOG_FILE, ERROR_LOG_FILE, LOG_DIR


class LoggingManager:
    """Handles IP-change logging, error logging, auto-purge, and paginated reads."""

    DATE_FMT = "%d/%m/%Y"
    TIME_FMT = "%H:%M:%S"
    COLUMNS = ("Date", "Time", "Target", "Detected", "Changed", "Manual")
    ERROR_MAX_SIZE = 1_048_576  # 1 MB rotation threshold

    def __init__(self, retention_days: int = 60):
        self.retention_days = retention_days
        self._lock = threading.Lock()
        os.makedirs(LOG_DIR, exist_ok=True)
        # Run purge in background so it doesn't block app launch
        threading.Thread(target=self.auto_purge, daemon=True).start()

    # ── Writing ──────────────────────────────────────────────────────────

    def log_ip(self, target_ip: str, detected_ip: str, changed: bool, manual: bool = False) -> None:
        now = datetime.datetime.now()
        row = [
            now.strftime(self.DATE_FMT),
            now.strftime(self.TIME_FMT),
            target_ip,
            detected_ip,
            "Yes" if changed else "No",
            "Yes" if manual else "No",
        ]
        with self._lock:
            with open(LOG_FILE, "a", newline="", encoding="utf-8") as fh:
                csv.writer(fh, delimiter="|").writerow(row)

    def log_error(self, error: Exception) -> None:
        """Append an error with traceback, rotating if the file is too large."""
        try:
            self._rotate_error_log()
            with open(ERROR_LOG_FILE, "a", encoding="utf-8") as fh:
                fh.write(f"[{datetime.datetime.now()}] {error}\n{traceback.format_exc()}\n")
        except Exception:
            pass  # Last-resort: swallow so the app doesn't crash

    # ── Auto-purge ───────────────────────────────────────────────────────

    def auto_purge(self) -> None:
        """Remove log entries older than `retention_days`."""
        if not os.path.isfile(LOG_FILE):
            return
        cutoff = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        kept: list[list[str]] = []
        with self._lock:
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as fh:
                    for row in csv.reader(fh, delimiter="|"):
                        if len(row) >= 6:
                            try:
                                entry_date = datetime.datetime.strptime(row[0], self.DATE_FMT)
                                if entry_date >= cutoff:
                                    kept.append(row)
                            except ValueError:
                                kept.append(row)  # keep unparsable rows
                with open(LOG_FILE, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh, delimiter="|")
                    for row in kept:
                        writer.writerow(row)
            except Exception as e:
                self.log_error(e)

    def purge_logs(self, mode: str) -> int:
        """Purge log entries based on mode. Returns count of removed rows.

        Modes:
            'last_7'    – delete entries older than 7 days
            'last_30'   – delete entries older than 30 days
            'all'       – delete all entries
            'unchanged' – delete entries where Changed == 'No'
        """
        if not os.path.isfile(LOG_FILE):
            return 0

        if mode == "all":
            with self._lock:
                try:
                    original = sum(1 for _ in open(LOG_FILE, "r", encoding="utf-8"))
                    with open(LOG_FILE, "w", newline="", encoding="utf-8") as fh:
                        pass  # truncate
                    return original
                except Exception as e:
                    self.log_error(e)
                    return 0

        now = datetime.datetime.now()
        kept: list[list[str]] = []
        total = 0

        with self._lock:
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as fh:
                    for row in csv.reader(fh, delimiter="|"):
                        if len(row) < 6:
                            continue
                        total += 1

                        if mode == "unchanged":
                            # Keep rows where Changed == "Yes"
                            if row[4].strip() == "Yes":
                                kept.append(row)
                        elif mode in ("last_7", "last_30"):
                            days = 7 if mode == "last_7" else 30
                            cutoff = now - datetime.timedelta(days=days)
                            try:
                                entry_date = datetime.datetime.strptime(row[0], self.DATE_FMT)
                                if entry_date >= cutoff:
                                    kept.append(row)
                            except ValueError:
                                kept.append(row)
                        else:
                            kept.append(row)

                with open(LOG_FILE, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh, delimiter="|")
                    for row in kept:
                        writer.writerow(row)

                return total - len(kept)
            except Exception as e:
                self.log_error(e)
                return 0

    # ── Paginated reading ────────────────────────────────────────────────

    def count_rows(self, search: str = "", changed_only: bool = False) -> int:
        """Return total row count matching the filter (without loading all into memory)."""
        if not os.path.isfile(LOG_FILE):
            return 0
        count = 0
        search_lower = search.lower()
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as fh:
                for row in csv.reader(fh, delimiter="|"):
                    if len(row) >= 6 and self._matches(row, search_lower, changed_only):
                        count += 1
        except Exception:
            pass
        return count

    def read_page(
        self,
        page: int = 1,
        page_size: int = 200,
        search: str = "",
        changed_only: bool = False,
        reverse: bool = True,
    ) -> list[list[str]]:
        """Return a page of log rows, newest-first by default."""
        if not os.path.isfile(LOG_FILE):
            return []

        search_lower = search.lower()
        all_matching: list[list[str]] = []
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as fh:
                for row in csv.reader(fh, delimiter="|"):
                    if len(row) >= 6 and self._matches(row, search_lower, changed_only):
                        all_matching.append(row)
        except Exception:
            return []

        if reverse:
            all_matching.reverse()

        start = (page - 1) * page_size
        return all_matching[start : start + page_size]

    def read_all_filtered(self, search: str = "", changed_only: bool = False) -> list[list[str]]:
        """Read all matching rows (used for CSV export)."""
        return self.read_page(page=1, page_size=999_999_999, search=search, changed_only=changed_only, reverse=False)

    # ── Private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _matches(row: list[str], search_lower: str, changed_only: bool) -> bool:
        if changed_only and row[4] != "Yes":
            return False
        if search_lower and search_lower not in "|".join(row).lower():
            return False
        return True

    def _rotate_error_log(self) -> None:
        try:
            if os.path.isfile(ERROR_LOG_FILE) and os.path.getsize(ERROR_LOG_FILE) > self.ERROR_MAX_SIZE:
                rotated = ERROR_LOG_FILE + ".old"
                if os.path.isfile(rotated):
                    os.remove(rotated)
                os.rename(ERROR_LOG_FILE, rotated)
        except Exception:
            pass
