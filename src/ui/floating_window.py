"""
TRIP — Modern draggable floating IP status window.
"""

import tkinter as tk


# ── Colour palette (matching settings) ───────────────────────────────────────
BG_DARK    = "#0f0f1a"
BG_CARD    = "#1e1e3a"
FG_PRIMARY = "#e2e8f0"
GREEN      = "#22c55e"
GREEN_BG   = "#0a2e1a"
RED        = "#ef4444"
RED_BG     = "#2e0a0a"
ACCENT     = "#6366f1"
BORDER     = "#2a2a48"


class FloatingWindow(tk.Toplevel):
    """A small, borderless, always-on-top window showing the current IP."""

    def __init__(self, master, config):
        super().__init__(master)
        self._config = config

        # Borderless, topmost
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", float(config.window_alpha))

        x = config.window_x
        y = config.window_y
        self.geometry(f"+{x}+{y}")

        # Main container with border effect
        self.configure(bg=ACCENT)

        self._outer = tk.Frame(self, bg=ACCENT, padx=1, pady=1)
        self._outer.pack()

        self._inner = tk.Frame(self._outer, bg=BG_DARK, padx=0, pady=0)
        self._inner.pack()

        # Status indicator dot
        self._header = tk.Frame(self._inner, bg=BG_DARK, padx=8, pady=3)
        self._header.pack(fill="x")

        self._dot = tk.Label(
            self._header, text="●", font=("Segoe UI", 8),
            bg=BG_DARK, fg=ACCENT,
        )
        self._dot.pack(side="left")

        self._status_label = tk.Label(
            self._header, text="TRIP", font=("Segoe UI", 7, "bold"),
            bg=BG_DARK, fg="#64748b",
        )
        self._status_label.pack(side="left", padx=(4, 0))

        # IP display
        self._ip_frame = tk.Frame(self._inner, bg=BG_CARD, padx=10, pady=5)
        self._ip_frame.pack(fill="x")

        self._label = tk.Label(
            self._ip_frame,
            text="checking…",
            font=("Cascadia Code", 11, "bold"),
            fg=FG_PRIMARY,
            bg=BG_CARD,
        )
        self._label.pack()

        # Dragging — bind all child widgets
        self._all_widgets = [self, self._outer, self._inner, self._header,
                       self._dot, self._status_label, self._ip_frame, self._label]
        for widget in self._all_widgets:
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<ButtonRelease-1>", self._end_drag)

        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self._drag_sx = 0
        self._drag_sy = 0

        # Flash state
        self._flashing = False
        self._flash_after_id = None
        self._flash_on = False
        self._last_border_color = ACCENT
        self._last_card_bg = BG_CARD

    # ── Drag handlers ────────────────────────────────────────────────────

    def _start_drag(self, event):
        self._drag_sx = event.x_root - self.winfo_x()
        self._drag_sy = event.y_root - self.winfo_y()
        # Stop flashing on click
        if self._flashing:
            self.stop_flashing()

    def _on_drag(self, event):
        x = event.x_root - self._drag_sx
        y = event.y_root - self._drag_sy
        self.geometry(f"+{x}+{y}")

    def _end_drag(self, _event):
        """Save position only on release."""
        self._config.set("window_x", str(self.winfo_x()))
        self._config.set("window_y", str(self.winfo_y()))
        self._config.save()

    # ── Flash animation ──────────────────────────────────────────────────

    def start_flashing(self) -> None:
        """Begin flashing the window border/background to attract attention."""
        if self._flashing:
            return
        self._flashing = True
        self._flash_on = False
        self._do_flash()

    def stop_flashing(self) -> None:
        """Stop flashing and restore normal colours."""
        self._flashing = False
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
            self._flash_after_id = None
        # Restore to last known state
        self._outer.config(bg=self._last_border_color)
        self.configure(bg=self._last_border_color)
        self._ip_frame.config(bg=self._last_card_bg)

    def _do_flash(self) -> None:
        """Toggle between flash colour and normal colour."""
        if not self._flashing or not self.winfo_exists():
            return
        self._flash_on = not self._flash_on
        if self._flash_on:
            # Bright flash state
            flash_border = "#f59e0b"  # Amber
            flash_bg = "#422006"      # Dark amber
            self._outer.config(bg=flash_border)
            self.configure(bg=flash_border)
            self._ip_frame.config(bg=flash_bg)
            self.attributes("-alpha", 1.0)
        else:
            # Normal state
            self._outer.config(bg=self._last_border_color)
            self.configure(bg=self._last_border_color)
            self._ip_frame.config(bg=self._last_card_bg)
        self._flash_after_id = self.after(400, self._do_flash)

    # ── Update display ───────────────────────────────────────────────────

    def update_ip(self, ip: str, target_ip: str) -> None:
        """Update the displayed IP and colour based on match status."""
        match = ip == target_ip

        if match:
            dot_fg = GREEN
            ip_fg = GREEN
            border_color = GREEN
            card_bg = GREEN_BG
            status_text = "MATCH"
        else:
            dot_fg = RED
            ip_fg = RED
            border_color = RED
            card_bg = RED_BG
            status_text = "MISMATCH"

        # Store for flash restore
        self._last_border_color = border_color
        self._last_card_bg = card_bg

        self._dot.config(fg=dot_fg)
        self._status_label.config(text=f"TRIP — {status_text}")
        self._label.config(text=ip, fg=ip_fg, bg=card_bg)

        # Only update border/bg if not currently flashing
        if not self._flashing:
            self._ip_frame.config(bg=card_bg)
            self._outer.config(bg=border_color)
            self.configure(bg=border_color)

        alpha = float(self._config.window_alpha) if match else 1.0
        if not self._flashing:
            self.attributes("-alpha", alpha)

    def show_error(self) -> None:
        """Show an error/unavailable state when IP lookup fails."""
        YELLOW = "#eab308"
        YELLOW_BG = "#2e2a0a"

        self._last_border_color = YELLOW
        self._last_card_bg = YELLOW_BG

        self._dot.config(fg=YELLOW)
        self._status_label.config(text="TRIP — UNAVAILABLE")
        self._label.config(text="no connection", fg=YELLOW, bg=YELLOW_BG)

        if not self._flashing:
            self._ip_frame.config(bg=YELLOW_BG)
            self._outer.config(bg=YELLOW)
            self.configure(bg=YELLOW)
            self.attributes("-alpha", 1.0)

