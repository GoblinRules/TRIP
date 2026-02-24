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
        for widget in [self, self._outer, self._inner, self._header,
                       self._dot, self._status_label, self._ip_frame, self._label]:
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<ButtonRelease-1>", self._end_drag)

        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self._drag_sx = 0
        self._drag_sy = 0

    # ── Drag handlers ────────────────────────────────────────────────────

    def _start_drag(self, event):
        self._drag_sx = event.x_root - self.winfo_x()
        self._drag_sy = event.y_root - self.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_sx
        y = event.y_root - self._drag_sy
        self.geometry(f"+{x}+{y}")

    def _end_drag(self, _event):
        """Save position only on release."""
        self._config.set("window_x", str(self.winfo_x()))
        self._config.set("window_y", str(self.winfo_y()))
        self._config.save()

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

        self._dot.config(fg=dot_fg)
        self._status_label.config(text=f"TRIP — {status_text}")
        self._label.config(text=ip, fg=ip_fg, bg=card_bg)
        self._ip_frame.config(bg=card_bg)
        self._outer.config(bg=border_color)
        self.configure(bg=border_color)

        alpha = float(self._config.window_alpha) if match else 1.0
        self.attributes("-alpha", alpha)
