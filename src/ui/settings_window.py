"""
TRIP — Settings window with modern, polished dark UI.
"""

from __future__ import annotations

import math
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, BooleanVar, StringVar, messagebox
import csv
import webbrowser

from ..constants import APP_DISPLAY_NAME, APP_VERSION, ICON_PNG
from ..logging_manager import LoggingManager

# ── Colour palette ───────────────────────────────────────────────────────────
BG_DARK       = "#0f0f1a"
BG_PANEL      = "#16162a"
BG_CARD       = "#1e1e3a"
BG_INPUT      = "#252548"
BG_HOVER      = "#2a2a52"
BG_ACCENT     = "#6366f1"   # Indigo accent
BG_ACCENT_HOV = "#818cf8"
FG_PRIMARY    = "#e2e8f0"
FG_SECONDARY  = "#94a3b8"
FG_MUTED      = "#64748b"
FG_ACCENT     = "#a5b4fc"
BORDER_SUBTLE = "#2a2a48"
GREEN_BADGE   = "#22c55e"
RED_BADGE     = "#ef4444"
SELECTION_BG  = "#3b3b6e"


class SettingsWindow:
    """Modern settings dialog with General, Logs, and About tabs."""

    PAGE_SIZE = 200

    def __init__(self, master: tk.Tk, config, logger: LoggingManager, on_save=None, on_close_app=None):
        self._master = master
        self._config = config
        self._logger = logger
        self._on_save = on_save
        self._on_close_app = on_close_app
        self._win: tk.Toplevel | None = None

    def show(self) -> None:
        if self._win and self._win.winfo_exists():
            self._win.lift()
            self._win.focus_force()
            return
        self._build()

    def is_open(self) -> bool:
        return self._win is not None and self._win.winfo_exists()

    def destroy(self) -> None:
        if self._win and self._win.winfo_exists():
            self._win.destroy()
        self._win = None

    # ── Build ────────────────────────────────────────────────────────────

    def _build(self) -> None:
        win = tk.Toplevel(self._master)
        self._win = win
        win.title(f"{APP_DISPLAY_NAME}")
        win.geometry("880x620")
        win.minsize(700, 480)
        win.configure(bg=BG_DARK)
        win.protocol("WM_DELETE_WINDOW", self._on_close)

        # Try to set the window icon
        try:
            if os.path.isfile(ICON_PNG):
                icon_img = tk.PhotoImage(file=ICON_PNG)
                win.iconphoto(False, icon_img)
                self._icon_ref = icon_img  # prevent GC
        except Exception:
            pass

        self._apply_styles(win)

        # ── Header bar ───────────────────────────────────────────────
        header = tk.Frame(win, bg=BG_PANEL, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="⚙", font=("Segoe UI", 18), bg=BG_PANEL,
                 fg=BG_ACCENT).pack(side="left", padx=(16, 6), pady=8)
        tk.Label(header, text="Settings", font=("Segoe UI Semibold", 15),
                 bg=BG_PANEL, fg=FG_PRIMARY).pack(side="left", pady=8)

        # Save button in header (just saves, doesn't close)
        save_btn = tk.Label(
            header, text="  💾  Save  ", font=("Segoe UI Semibold", 10),
            bg=BG_ACCENT, fg="#ffffff", cursor="hand2",
            padx=16, pady=6,
        )
        save_btn.pack(side="right", padx=16, pady=12)
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg=BG_ACCENT_HOV))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg=BG_ACCENT))
        save_btn.bind("<Button-1>", lambda e: self._save())

        # Thin accent line
        tk.Frame(win, bg=BG_ACCENT, height=2).pack(fill="x")

        # ── Custom tab bar (uniform size) ────────────────────────────
        tab_bar = tk.Frame(win, bg=BG_DARK)
        tab_bar.pack(fill="x", padx=12, pady=(10, 0))

        self._tab_frames = {}  # name -> content frame
        self._tab_btns = {}    # name -> label widget
        self._current_tab = None

        # Content container
        self._content = tk.Frame(win, bg=BG_PANEL)
        self._content.pack(expand=True, fill="both", padx=12, pady=(4, 12))

        # Build tab buttons — all uniform width
        tabs = [
            ("General", "⚡"),
            ("Logs", "📋"),
            ("About", "ℹ️"),
        ]
        for name, icon in tabs:
            btn = tk.Label(
                tab_bar, text=f"  {icon}  {name}  ",
                font=("Segoe UI Semibold", 10),
                bg=BG_CARD, fg=FG_SECONDARY,
                padx=24, pady=8, cursor="hand2",
                highlightbackground=BORDER_SUBTLE, highlightthickness=1,
            )
            btn.pack(side="left", padx=(0, 2))
            btn.bind("<Button-1>", lambda e, n=name: self._switch_tab(n))
            btn.bind("<Enter>", lambda e, b=btn, n=name: (
                b.config(bg=BG_HOVER) if n != self._current_tab else None
            ))
            btn.bind("<Leave>", lambda e, b=btn, n=name: (
                b.config(bg=BG_CARD) if n != self._current_tab else None
            ))
            self._tab_btns[name] = btn

        # Build tab content frames
        for name, _ in tabs:
            frame = tk.Frame(self._content, bg=BG_PANEL)
            self._tab_frames[name] = frame

        self._build_general(self._tab_frames["General"])
        self._build_logs(self._tab_frames["Logs"])
        self._build_about(self._tab_frames["About"])

        # Show first tab
        self._switch_tab("General")

    def _switch_tab(self, name: str) -> None:
        """Switch to the specified tab."""
        if self._current_tab == name:
            return

        # Hide current
        if self._current_tab and self._current_tab in self._tab_frames:
            self._tab_frames[self._current_tab].pack_forget()
            self._tab_btns[self._current_tab].config(
                bg=BG_CARD, fg=FG_SECONDARY,
                highlightbackground=BORDER_SUBTLE,
            )

        # Show new
        self._current_tab = name
        self._tab_frames[name].pack(fill="both", expand=True)
        self._tab_btns[name].config(
            bg=BG_ACCENT, fg="#ffffff",
            highlightbackground=BG_ACCENT,
        )

    def _apply_styles(self, win) -> None:
        style = ttk.Style(win)
        style.theme_use("clam")

        # Frames
        style.configure("TFrame", background=BG_PANEL)
        style.configure("Card.TFrame", background=BG_PANEL)

        # Labels
        style.configure("TLabel", background=BG_PANEL, foreground=FG_PRIMARY,
                        font=("Segoe UI", 10))

        # Treeview
        style.configure("Treeview",
                        background=BG_CARD, foreground=FG_PRIMARY,
                        fieldbackground=BG_CARD, rowheight=28,
                        font=("Segoe UI", 9), borderwidth=0)
        style.configure("Treeview.Heading",
                        background=BG_INPUT, foreground=FG_ACCENT,
                        font=("Segoe UI Semibold", 9),
                        borderwidth=0, relief="flat")
        style.map("Treeview",
                  background=[("selected", SELECTION_BG)],
                  foreground=[("selected", "#ffffff")])

        # Scrollbar
        style.configure("Vertical.TScrollbar",
                        background=BG_CARD, troughcolor=BG_PANEL,
                        borderwidth=0, arrowsize=12)
        style.map("Vertical.TScrollbar",
                  background=[("active", BG_HOVER)])

    # ── Helpers ──────────────────────────────────────────────────────────

    def _make_scrollable(self, parent) -> tk.Frame:
        """Create a scrollable frame inside parent. Returns the inner frame."""
        canvas = tk.Canvas(parent, bg=BG_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_PANEL)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_frame = canvas.create_window((0, 0), window=inner, anchor="nw")

        # Make inner frame stretch to canvas width
        def _on_canvas_resize(e):
            canvas.itemconfig(canvas_frame, width=e.width)
        canvas.bind("<Configure>", _on_canvas_resize)

        canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        inner.bind("<MouseWheel>", _on_mousewheel)

        # Bind mousewheel to all children recursively
        def _bind_wheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_wheel(child)

        # We'll call _bind_wheel after building the content
        canvas._bind_wheel = _bind_wheel

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner._canvas = canvas
        return inner

    def _make_section(self, parent, title, row=0) -> tk.Frame:
        """Create a styled section card inside a tab."""
        section = tk.Frame(parent, bg=BG_CARD, padx=16, pady=12,
                          highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        section.pack(fill="x", padx=16, pady=(12 if row == 0 else 6, 0))

        tk.Label(section, text=title, font=("Segoe UI Semibold", 11),
                bg=BG_CARD, fg=FG_ACCENT).pack(anchor="w")
        tk.Frame(section, bg=BORDER_SUBTLE, height=1).pack(fill="x", pady=(6, 8))
        return section

    def _make_field(self, parent, label, default="", width=28) -> tk.Entry:
        """Create a label + entry field pair."""
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, font=("Segoe UI", 10), bg=BG_CARD,
                fg=FG_SECONDARY, width=28, anchor="w").pack(side="left")
        entry = tk.Entry(row, font=("Segoe UI", 10), bg=BG_INPUT, fg=FG_PRIMARY,
                        insertbackground=FG_PRIMARY, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=BORDER_SUBTLE,
                        highlightcolor=BG_ACCENT, width=width)
        entry.insert(0, default)
        entry.pack(side="left", ipady=4, padx=(4, 0))
        return entry

    def _make_toggle(self, parent, label, variable) -> tk.Checkbutton:
        """Create a styled toggle row."""
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", pady=3)
        cb = tk.Checkbutton(
            row, text=f"  {label}", variable=variable,
            font=("Segoe UI", 10), bg=BG_CARD, fg=FG_PRIMARY,
            selectcolor=BG_INPUT, activebackground=BG_CARD,
            activeforeground=FG_PRIMARY, highlightthickness=0,
            bd=0, anchor="w",
        )
        cb.pack(anchor="w")
        return cb

    # ── General tab ──────────────────────────────────────────────────────

    def _build_general(self, parent: tk.Frame) -> None:
        inner = self._make_scrollable(parent)

        # ── IP Monitoring section
        sec1 = self._make_section(inner, "🌐  IP Monitoring", row=0)
        self._ip_entry = self._make_field(sec1, "Target IP Address", self._config.target_ip)
        self._interval_entry = self._make_field(sec1, "Check interval (seconds)", str(self._config.check_interval), width=10)

        # ── Preferences section
        sec2 = self._make_section(inner, "🔧  Preferences", row=1)
        self._notify_var = BooleanVar(value=self._config.notify_on_change)
        self._log_var = BooleanVar(value=self._config.enable_logging)
        self._screen_var = BooleanVar(value=self._config.always_on_screen)

        self._make_toggle(sec2, "Send notification on IP change", self._notify_var)
        self._make_toggle(sec2, "Enable IP change logging", self._log_var)
        self._make_toggle(sec2, "Show floating IP overlay on launch", self._screen_var)

        # ── Data Management section
        sec3 = self._make_section(inner, "🗄  Data Management", row=2)
        self._retention_entry = self._make_field(sec3, "Log retention (days, 1–365)", str(self._config.log_retention_days), width=10)

        # Hint text
        tk.Label(sec3, text="Logs older than this are automatically purged on startup.",
                font=("Segoe UI", 9), bg=BG_CARD, fg=FG_MUTED).pack(anchor="w", pady=(2, 0))

        # ── IP Change Actions section
        sec4 = self._make_section(inner, "⚡  IP Change Actions", row=3)

        self._flash_var = BooleanVar(value=self._config.flash_on_change)
        self._close_browsers_var = BooleanVar(value=self._config.close_browsers_on_change)
        self._restart_var = BooleanVar(value=self._config.restart_on_change)

        self._make_toggle(sec4, "Flash floating window on IP change", self._flash_var)
        tk.Label(sec4, text="The overlay will flash amber until you click it.",
                font=("Segoe UI", 9), bg=BG_CARD, fg=FG_MUTED).pack(anchor="w", pady=(0, 4))

        self._make_toggle(sec4, "Close all browsers on IP change", self._close_browsers_var)
        tk.Label(sec4, text="⚠  Forcefully closes Chrome, Firefox, Edge, Brave, Opera & Vivaldi.",
                font=("Segoe UI", 9), bg=BG_CARD, fg="#fbbf24").pack(anchor="w", pady=(0, 4))

        self._make_toggle(sec4, "Restart PC on IP change", self._restart_var)
        tk.Label(sec4, text="⚠  The PC will restart after a 5-second grace period.",
                font=("Segoe UI", 9), bg=BG_CARD, fg="#f87171").pack(anchor="w", pady=(0, 4))

        # Bind mouse wheel after building
        inner._canvas._bind_wheel(inner)

    # ── Logs tab ─────────────────────────────────────────────────────────

    def _build_logs(self, parent: tk.Frame) -> None:
        # Controls bar
        ctrl = tk.Frame(parent, bg=BG_PANEL)
        ctrl.pack(fill="x", padx=12, pady=(10, 4))

        # Search field
        search_frame = tk.Frame(ctrl, bg=BG_INPUT, highlightbackground=BORDER_SUBTLE,
                               highlightthickness=1, highlightcolor=BG_ACCENT)
        search_frame.pack(side="left", fill="x", expand=True, ipady=3)

        tk.Label(search_frame, text=" 🔍 ", bg=BG_INPUT, fg=FG_MUTED,
                font=("Segoe UI", 10)).pack(side="left")
        self._search_var = StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self._search_var,
                               font=("Segoe UI", 10), bg=BG_INPUT, fg=FG_PRIMARY,
                               insertbackground=FG_PRIMARY, relief="flat", bd=0)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Changed only toggle
        self._changed_only_var = BooleanVar(value=False)
        tk.Checkbutton(ctrl, text=" Changed only", variable=self._changed_only_var,
                      font=("Segoe UI", 9), bg=BG_PANEL, fg=FG_SECONDARY,
                      selectcolor=BG_INPUT, activebackground=BG_PANEL,
                      command=self._reset_and_load_logs).pack(side="left", padx=(10, 4))

        # Action buttons
        btn_frame = tk.Frame(ctrl, bg=BG_PANEL)
        btn_frame.pack(side="right")

        for text, cmd in [("Refresh", self._reset_and_load_logs), ("Export CSV", self._export_logs)]:
            btn = tk.Label(btn_frame, text=f" {text} ", font=("Segoe UI", 9),
                          bg=BG_CARD, fg=FG_SECONDARY, cursor="hand2",
                          padx=10, pady=4,
                          highlightbackground=BORDER_SUBTLE, highlightthickness=1)
            btn.pack(side="left", padx=3)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BG_HOVER, fg=FG_PRIMARY))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG_CARD, fg=FG_SECONDARY))
            btn.bind("<Button-1>", lambda e, c=cmd: c())

        # Purge button (red tinted)
        purge_btn = tk.Label(btn_frame, text=" 🗑 Purge ", font=("Segoe UI", 9),
                            bg="#2e1420", fg="#f87171", cursor="hand2",
                            padx=10, pady=4,
                            highlightbackground="#5c2030", highlightthickness=1)
        purge_btn.pack(side="left", padx=3)
        purge_btn.bind("<Enter>", lambda e: purge_btn.config(bg="#4a1a2e", fg="#fca5a5"))
        purge_btn.bind("<Leave>", lambda e: purge_btn.config(bg="#2e1420", fg="#f87171"))
        purge_btn.bind("<Button-1>", lambda e: self._purge_dialog())

        # Treeview with scrollbar
        tree_frame = tk.Frame(parent, bg=BG_PANEL)
        tree_frame.pack(expand=True, fill="both", padx=12, pady=4)

        columns = ("Date", "Time", "Target", "Detected", "Changed", "Manual")
        self._log_tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                       selectmode="extended")
        col_widths = {"Date": 95, "Time": 80, "Target": 130, "Detected": 130, "Changed": 75, "Manual": 70}
        for col in columns:
            self._log_tree.heading(col, text=col, command=lambda c=col: self._sort_column(c, False))
            self._log_tree.column(col, width=col_widths.get(col, 100), minwidth=50)

        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self._log_tree.yview)
        self._log_tree.configure(yscrollcommand=y_scroll.set)
        self._log_tree.pack(side="left", expand=True, fill="both")
        y_scroll.pack(side="right", fill="y")

        # Pagination bar
        page_bar = tk.Frame(parent, bg=BG_PANEL)
        page_bar.pack(fill="x", padx=12, pady=(0, 8))

        self._page_label = tk.Label(page_bar, text="Page 1 of 1",
                                    bg=BG_PANEL, fg=FG_MUTED,
                                    font=("Segoe UI", 9))
        self._page_label.pack(side="left")

        for text, cmd in [("Next ▶", self._next_page), ("◀ Prev", self._prev_page)]:
            btn = tk.Label(page_bar, text=f" {text} ", font=("Segoe UI", 9),
                          bg=BG_CARD, fg=FG_SECONDARY, cursor="hand2",
                          padx=8, pady=3,
                          highlightbackground=BORDER_SUBTLE, highlightthickness=1)
            btn.pack(side="right", padx=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BG_HOVER, fg=FG_PRIMARY))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG_CARD, fg=FG_SECONDARY))
            btn.bind("<Button-1>", lambda e, c=cmd: c())

        self._current_page = 1
        self._total_pages = 1

        # Debounced search
        self._search_var.trace_add("write", lambda *_: self._debounce_search())
        self._search_timer = None

        self._reset_and_load_logs()

    def _debounce_search(self) -> None:
        if self._search_timer is not None:
            self._win.after_cancel(self._search_timer)
        self._search_timer = self._win.after(300, self._reset_and_load_logs)

    def _reset_and_load_logs(self) -> None:
        self._current_page = 1
        self._load_logs()

    def _load_logs(self) -> None:
        search = self._search_var.get() if hasattr(self, "_search_var") else ""
        changed_only = self._changed_only_var.get() if hasattr(self, "_changed_only_var") else False
        page = self._current_page

        def _bg():
            total = self._logger.count_rows(search=search, changed_only=changed_only)
            rows = self._logger.read_page(
                page=page, page_size=self.PAGE_SIZE,
                search=search, changed_only=changed_only, reverse=True,
            )
            total_pages = max(1, math.ceil(total / self.PAGE_SIZE))
            if self._win and self._win.winfo_exists():
                self._win.after(0, lambda: self._populate_tree(rows, page, total_pages))

        threading.Thread(target=_bg, daemon=True).start()

    def _populate_tree(self, rows: list, page: int, total_pages: int) -> None:
        tree = self._log_tree
        tree.delete(*tree.get_children())
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))

        tree.tag_configure("even", background=BG_CARD)
        tree.tag_configure("odd", background=BG_PANEL)

        self._total_pages = total_pages
        self._current_page = page
        self._page_label.config(text=f"Page {page} of {total_pages}")

    def _next_page(self) -> None:
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._load_logs()

    def _prev_page(self) -> None:
        if self._current_page > 1:
            self._current_page -= 1
            self._load_logs()

    def _sort_column(self, col: str, reverse: bool) -> None:
        data = [(self._log_tree.set(k, col), k) for k in self._log_tree.get_children("")]
        data.sort(reverse=reverse)
        for i, (_, k) in enumerate(data):
            self._log_tree.move(k, "", i)
        self._log_tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _export_logs(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export Logs",
        )
        if not path:
            return
        search = self._search_var.get()
        changed_only = self._changed_only_var.get()
        rows = self._logger.read_all_filtered(search=search, changed_only=changed_only)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Date", "Time", "Target", "Detected", "Changed", "Manual"])
            for row in rows:
                writer.writerow(row)

    # ── Purge ─────────────────────────────────────────────────────────────

    def _purge_dialog(self) -> None:
        """Show a styled purge options panel (borderless, no modal behavior)."""
        # Dismiss any existing purge panel
        if hasattr(self, '_purge_panel') and self._purge_panel and self._purge_panel.winfo_exists():
            self._purge_panel.destroy()
            self._purge_panel = None
            return

        dlg = tk.Toplevel(self._master)
        dlg.overrideredirect(True)
        dlg.configure(bg=BORDER_SUBTLE)
        dlg.attributes("-topmost", True)
        self._purge_panel = dlg

        frame = tk.Frame(dlg, bg=BG_DARK, padx=24, pady=20)
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Header
        tk.Label(frame, text="\U0001f5d1  Purge Logs", font=("Segoe UI", 13, "bold"),
                 bg=BG_DARK, fg=FG_PRIMARY).pack(anchor="w")
        tk.Label(frame, text="Choose which log entries to remove:",
                 font=("Segoe UI", 9), bg=BG_DARK, fg=FG_SECONDARY).pack(anchor="w", pady=(2, 14))

        options = [
            ("Older than 7 days",   "last_7",    "Remove entries older than 7 days"),
            ("Older than 30 days",  "last_30",   "Remove entries older than 30 days"),
            ("Unchanged IP only",   "unchanged", "Remove entries where IP didn't change"),
            ("All logs",            "all",       "Delete every log entry"),
        ]

        for label, mode, desc in options:
            is_danger = mode == "all"
            btn_bg = "#2e1420" if is_danger else BG_CARD
            btn_fg = "#f87171" if is_danger else FG_PRIMARY
            btn_hover_bg = "#4a1a2e" if is_danger else BG_HOVER
            btn_border = "#5c2030" if is_danger else BORDER_SUBTLE

            row = tk.Frame(frame, bg=btn_bg, cursor="hand2",
                          highlightbackground=btn_border, highlightthickness=1)
            row.pack(fill="x", pady=3)

            txt_frame = tk.Frame(row, bg=btn_bg)
            txt_frame.pack(fill="x", padx=14, pady=8)

            title_lbl = tk.Label(txt_frame, text=label, font=("Segoe UI", 10, "bold"),
                                bg=btn_bg, fg=btn_fg, anchor="w")
            title_lbl.pack(fill="x")

            desc_lbl = tk.Label(txt_frame, text=desc, font=("Segoe UI", 8),
                               bg=btn_bg, fg=FG_MUTED, anchor="w")
            desc_lbl.pack(fill="x")

            # Hover and click closures
            def mk_enter(r, tf, tl, dl, hbg=btn_hover_bg):
                def fn(e):
                    for w in (r, tf, tl, dl):
                        w.configure(bg=hbg)
                return fn

            def mk_leave(r, tf, tl, dl, obg=btn_bg):
                def fn(e):
                    for w in (r, tf, tl, dl):
                        w.configure(bg=obg)
                return fn

            def mk_click(m):
                def fn(e):
                    self._win.after(10, lambda: self._confirm_purge(m))
                return fn

            for w in (row, txt_frame, title_lbl, desc_lbl):
                w.bind("<Enter>", mk_enter(row, txt_frame, title_lbl, desc_lbl))
                w.bind("<Leave>", mk_leave(row, txt_frame, title_lbl, desc_lbl))
                w.bind("<Button-1>", mk_click(mode))

        # Cancel
        cancel = tk.Label(frame, text="Cancel", font=("Segoe UI", 9),
                         bg=BG_DARK, fg=FG_MUTED, cursor="hand2", pady=8)
        cancel.pack(pady=(10, 0))
        cancel.bind("<Enter>", lambda e: cancel.config(fg=FG_PRIMARY))
        cancel.bind("<Leave>", lambda e: cancel.config(fg=FG_MUTED))
        cancel.bind("<Button-1>", lambda e: self._dismiss_purge_panel())

        # Dismiss on focus loss
        dlg.bind("<FocusOut>", lambda e: self._dismiss_purge_panel())

        # Position centered on settings window
        dlg.update_idletasks()
        dw = dlg.winfo_reqwidth()
        dh = dlg.winfo_reqheight()
        wx = self._win.winfo_x() + self._win.winfo_width() // 2 - dw // 2
        wy = self._win.winfo_y() + self._win.winfo_height() // 2 - dh // 2
        dlg.geometry(f"{dw}x{dh}+{wx}+{wy}")
        dlg.focus_force()

    def _dismiss_purge_panel(self) -> None:
        """Destroy the purge panel if it exists."""
        if hasattr(self, '_purge_panel') and self._purge_panel:
            try:
                if self._purge_panel.winfo_exists():
                    self._purge_panel.destroy()
            except Exception:
                pass
            self._purge_panel = None

    def _confirm_purge(self, mode: str) -> None:
        """Show inline confirmation then execute purge."""
        labels = {
            "last_7": "entries older than 7 days",
            "last_30": "entries older than 30 days",
            "unchanged": "entries where IP didn't change",
            "all": "ALL log entries",
        }

        # Dismiss the options panel first
        self._dismiss_purge_panel()

        # Create a confirmation panel
        dlg = tk.Toplevel(self._master)
        dlg.overrideredirect(True)
        dlg.configure(bg=BORDER_SUBTLE)
        dlg.attributes("-topmost", True)
        self._purge_panel = dlg

        frame = tk.Frame(dlg, bg=BG_DARK, padx=24, pady=20)
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Label(frame, text="\u26a0  Are you sure?", font=("Segoe UI", 13, "bold"),
                 bg=BG_DARK, fg="#fbbf24").pack(pady=(0, 8))
        tk.Label(frame, text=f"This will delete {labels.get(mode, mode)}.",
                 font=("Segoe UI", 10), bg=BG_DARK, fg=FG_SECONDARY).pack(pady=(0, 4))
        tk.Label(frame, text="This cannot be undone.",
                 font=("Segoe UI", 9), bg=BG_DARK, fg=FG_MUTED).pack(pady=(0, 16))

        btn_row = tk.Frame(frame, bg=BG_DARK)
        btn_row.pack()

        # Yes button (red)
        yes_btn = tk.Label(btn_row, text="  Yes, purge  ", font=("Segoe UI", 10, "bold"),
                          bg="#7f1d1d", fg="#fca5a5", cursor="hand2",
                          padx=16, pady=8,
                          highlightbackground="#991b1b", highlightthickness=1)
        yes_btn.pack(side="left", padx=6)
        yes_btn.bind("<Enter>", lambda e: yes_btn.config(bg="#991b1b"))
        yes_btn.bind("<Leave>", lambda e: yes_btn.config(bg="#7f1d1d"))
        yes_btn.bind("<Button-1>", lambda e: self._win.after(10, lambda: self._execute_purge(mode)))

        # No button
        no_btn = tk.Label(btn_row, text="  Cancel  ", font=("Segoe UI", 10),
                         bg=BG_CARD, fg=FG_SECONDARY, cursor="hand2",
                         padx=16, pady=8,
                         highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        no_btn.pack(side="left", padx=6)
        no_btn.bind("<Enter>", lambda e: no_btn.config(bg=BG_HOVER, fg=FG_PRIMARY))
        no_btn.bind("<Leave>", lambda e: no_btn.config(bg=BG_CARD, fg=FG_SECONDARY))
        no_btn.bind("<Button-1>", lambda e: self._dismiss_purge_panel())

        # Position centered on settings window
        dlg.update_idletasks()
        dw = dlg.winfo_reqwidth()
        dh = dlg.winfo_reqheight()
        wx = self._win.winfo_x() + self._win.winfo_width() // 2 - dw // 2
        wy = self._win.winfo_y() + self._win.winfo_height() // 2 - dh // 2
        dlg.geometry(f"{dw}x{dh}+{wx}+{wy}")
        dlg.focus_force()

    def _execute_purge(self, mode: str) -> None:
        """Run the purge in a background thread, then refresh logs."""
        self._dismiss_purge_panel()

        def _bg():
            self._logger.purge_logs(mode)
            if self._win and self._win.winfo_exists():
                self._win.after(0, self._reset_and_load_logs)

        threading.Thread(target=_bg, daemon=True).start()

    # ── About tab ────────────────────────────────────────────────────────

    def _build_about(self, parent: tk.Frame) -> None:
        inner = self._make_scrollable(parent)

        # App title card
        card = tk.Frame(inner, bg=BG_CARD, padx=24, pady=20,
                       highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        card.pack(fill="x", padx=16, pady=(12, 0))

        title_row = tk.Frame(card, bg=BG_CARD)
        title_row.pack(anchor="w")
        tk.Label(title_row, text="🛰️", font=("Segoe UI", 28), bg=BG_CARD,
                fg=FG_PRIMARY).pack(side="left", padx=(0, 12))

        title_text = tk.Frame(title_row, bg=BG_CARD)
        title_text.pack(side="left")
        tk.Label(title_text, text=APP_DISPLAY_NAME,
                font=("Segoe UI Semibold", 18), bg=BG_CARD, fg=FG_PRIMARY).pack(anchor="w")

        # Version badge
        ver_badge = tk.Label(title_text, text=f"  v{APP_VERSION}  ",
                            font=("Segoe UI Semibold", 9),
                            bg=BG_ACCENT, fg="#ffffff", padx=8, pady=2)
        ver_badge.pack(anchor="w", pady=(4, 0))

        # Separator
        tk.Frame(card, bg=BORDER_SUBTLE, height=1).pack(fill="x", pady=(16, 12))

        tk.Label(card, text="A lightweight system tray utility that monitors your\n"
                            "public IP address, logs changes, and notifies you\n"
                            "when your IP changes.",
                font=("Segoe UI", 10), bg=BG_CARD, fg=FG_SECONDARY,
                justify="left").pack(anchor="w")

        # Features list
        features_card = tk.Frame(inner, bg=BG_CARD, padx=24, pady=16,
                                highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        features_card.pack(fill="x", padx=16, pady=(10, 0))

        tk.Label(features_card, text="Features", font=("Segoe UI Semibold", 11),
                bg=BG_CARD, fg=FG_ACCENT).pack(anchor="w")

        features = [
            ("🔍", "Real-time IP monitoring with configurable intervals"),
            ("🔔", "Native Windows toast notifications on IP changes"),
            ("📊", "Searchable, paginated log viewer with CSV export"),
            ("🧹", "Automatic log purging based on retention settings"),
            ("📌", "Draggable floating overlay with colour-coded status"),
        ]
        for icon, text in features:
            row = tk.Frame(features_card, bg=BG_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=icon, font=("Segoe UI", 10), bg=BG_CARD,
                    fg=FG_PRIMARY).pack(side="left", padx=(0, 8))
            tk.Label(row, text=text, font=("Segoe UI", 9), bg=BG_CARD,
                    fg=FG_SECONDARY).pack(side="left")

        # GitHub link
        link_card = tk.Frame(inner, bg=BG_CARD, padx=24, pady=12,
                            highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        link_card.pack(fill="x", padx=16, pady=(10, 12))

        link = tk.Label(link_card, text="🔗  View on GitHub",
                       font=("Segoe UI", 10, "underline"), bg=BG_CARD,
                       fg=FG_ACCENT, cursor="hand2")
        link.pack(anchor="w")
        link.bind("<Button-1>", lambda _: webbrowser.open("https://github.com/GoblinRules"))
        link.bind("<Enter>", lambda e: link.config(fg=BG_ACCENT_HOV))
        link.bind("<Leave>", lambda e: link.config(fg=FG_ACCENT))

        # Bind mouse wheel after building
        inner._canvas._bind_wheel(inner)

    # ── Save (without closing) ───────────────────────────────────────────

    def _save(self) -> None:
        try:
            interval = max(5, min(3600, int(self._interval_entry.get().strip() or "60")))
        except ValueError:
            interval = 60

        try:
            retention = max(1, min(365, int(self._retention_entry.get().strip() or "60")))
        except ValueError:
            retention = 60

        self._config.set("target_ip", self._ip_entry.get().strip())
        self._config.set("check_interval", str(interval))
        self._config.set("notify_on_change", "yes" if self._notify_var.get() else "no")
        self._config.set("enable_logging", "yes" if self._log_var.get() else "no")
        self._config.set("always_on_screen", "yes" if self._screen_var.get() else "no")
        self._config.set("log_retention_days", str(retention))
        self._config.set("flash_on_change", "yes" if self._flash_var.get() else "no")
        self._config.set("close_browsers_on_change", "yes" if self._close_browsers_var.get() else "no")
        self._config.set("restart_on_change", "yes" if self._restart_var.get() else "no")
        self._config.save()
        self._config.reload()

        self._logger.retention_days = retention

        if self._on_save:
            self._on_save()

        # Brief flash to confirm save
        for btn in [self._tab_btns.get(self._current_tab)]:
            pass  # Could flash the save button instead
        # Show a saved indicator on the save button
        self._show_save_confirmation()

    def _show_save_confirmation(self) -> None:
        """Briefly change the header to show saved status."""
        if not self._win or not self._win.winfo_exists():
            return
        # Find the save button and flash it green
        for widget in self._win.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "Save" in str(child.cget("text")):
                        original_bg = child.cget("bg")
                        original_text = child.cget("text")
                        child.config(bg=GREEN_BADGE, text="  ✓  Saved!  ")
                        self._win.after(1500, lambda: (
                            child.config(bg=original_bg, text=original_text)
                            if self._win and self._win.winfo_exists() else None
                        ))
                        return

    def _on_close(self) -> None:
        """X button on settings — just close the settings window."""
        if self._win and self._win.winfo_exists():
            self._win.destroy()
        self._win = None
