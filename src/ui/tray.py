"""
TRIP — Native Win32 system‑tray icon with dark‑themed context menu.

Replaces pystray with direct Win32 API calls for full control over
icon size, menu, and tooltip.  Context menu uses tkinter for a
polished dark‑themed popup that matches the rest of the app.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
import sys
import threading
import tkinter as tk
import uuid
from typing import Callable, Optional

from PIL import Image

from ..constants import (
    ICON_DEFAULT, ICON_GREEN, ICON_RED,
    APP_DISPLAY_NAME,
)

# ───────────────────── Theme palette ───────────────────────────
_BG           = "#0f0f1a"
_BG_ITEM      = "#16162a"
_BG_HOVER     = "#2a2a52"
_BG_EXIT_HOVER = "#3b1420"
_FG           = "#e2e8f0"
_FG_MUTED     = "#94a3b8"
_FG_EXIT      = "#f87171"
_ACCENT       = "#6366f1"
_BORDER       = "#2a2a48"
_SEPARATOR    = "#252548"
_FONT_FAMILY  = "Segoe UI"
_FONT_SIZE    = 10

# ───────────────────── Win32 Constants ─────────────────────────
WM_USER        = 0x0400
WM_TRAYICON    = WM_USER + 20
WM_COMMAND     = 0x0111
WM_LBUTTONUP   = 0x0202
WM_RBUTTONUP   = 0x0205
WM_DESTROY     = 0x0002

NIM_ADD    = 0
NIM_MODIFY = 1
NIM_DELETE = 2

NIF_MESSAGE = 0x01
NIF_ICON    = 0x02
NIF_TIP     = 0x04

IMAGE_ICON       = 1
LR_LOADFROMFILE  = 0x0010

WS_OVERLAPPED = 0x00000000

SM_CXICON = 11
SM_CYICON = 12

# ───────────────────── Win32 API references ────────────────────
_user32_dll = ctypes.WinDLL("user32", use_last_error=True)
_shell32_dll = ctypes.WinDLL("shell32", use_last_error=True)
_kernel32_dll = ctypes.WinDLL("kernel32", use_last_error=True)

_DefWindowProcW = _user32_dll.DefWindowProcW
_DefWindowProcW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
_DefWindowProcW.restype = ctypes.c_void_p

WNDPROC_TYPE = ctypes.WINFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
    ctypes.c_void_p, ctypes.c_void_p,
)

# ───────────────────── Win32 Structures ────────────────────────

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize",           wt.DWORD),
        ("hWnd",             wt.HWND),
        ("uID",              wt.UINT),
        ("uFlags",           wt.UINT),
        ("uCallbackMessage", wt.UINT),
        ("hIcon",            wt.HICON),
        ("szTip",            wt.WCHAR * 128),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style",         wt.UINT),
        ("lpfnWndProc",   ctypes.c_void_p),
        ("cbClsExtra",    ctypes.c_int),
        ("cbWndExtra",    ctypes.c_int),
        ("hInstance",      wt.HINSTANCE),
        ("hIcon",          wt.HICON),
        ("hCursor",        wt.HICON),
        ("hbrBackground",  wt.HBRUSH),
        ("lpszMenuName",   wt.LPCWSTR),
        ("lpszClassName",  wt.LPCWSTR),
    ]


def _load_ico(path: str) -> int:
    if not os.path.isfile(path):
        return 0
    cx = _user32_dll.GetSystemMetrics(SM_CXICON) or 32
    cy = _user32_dll.GetSystemMetrics(SM_CYICON) or 32
    h = _user32_dll.LoadImageW(None, path, IMAGE_ICON, cx, cy, LR_LOADFROMFILE)
    return h or 0


# ───────────────────── TrayManager ─────────────────────────────

_active_tray: Optional["TrayManager"] = None


@WNDPROC_TYPE
def _wnd_proc(hwnd, msg, wparam, lparam):
    tray = _active_tray

    if msg == WM_TRAYICON:
        mouse_msg = (lparam or 0) & 0xFFFF
        if mouse_msg == WM_RBUTTONUP and tray:
            tray._show_context_menu()
            return 0

    elif msg == WM_DESTROY:
        _user32_dll.PostQuitMessage(0)
        return 0

    return _DefWindowProcW(hwnd, msg, wparam, lparam)


class TrayManager:
    """Native Win32 system‑tray icon with dark‑themed context menu."""

    _UID = 1

    def __init__(
        self,
        tk_root: tk.Tk | None = None,
        on_settings: Callable | None = None,
        on_toggle_overlay: Callable | None = None,
        on_recheck: Callable | None = None,
        on_exit: Callable | None = None,
    ):
        self._root = tk_root
        self._on_settings = on_settings
        self._on_toggle_overlay = on_toggle_overlay
        self._on_recheck = on_recheck
        self._on_exit = on_exit
        self._overlay_visible = False

        self._hwnd = None
        self._hicon = None
        self._nid: NOTIFYICONDATAW | None = None
        self._thread: threading.Thread | None = None
        self._class_name = f"TripTray_{uuid.uuid4().hex[:8]}"
        self._wndproc_ref = _wnd_proc
        self._popup: tk.Toplevel | None = None

    @property
    def overlay_visible(self) -> bool:
        return self._overlay_visible

    @overlay_visible.setter
    def overlay_visible(self, value: bool) -> None:
        self._overlay_visible = value

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self) -> None:
        global _active_tray
        _active_tray = self
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        hinstance = _kernel32_dll.GetModuleHandleW(None)

        wc = WNDCLASSW()
        wc.lpfnWndProc = ctypes.cast(_wnd_proc, ctypes.c_void_p).value
        wc.hInstance = hinstance
        wc.lpszClassName = self._class_name
        _user32_dll.RegisterClassW(ctypes.byref(wc))

        self._hwnd = _user32_dll.CreateWindowExW(
            0, self._class_name, "TRIP Tray", WS_OVERLAPPED,
            0, 0, 0, 0, None, None, hinstance, None,
        )

        self._hicon = _load_ico(ICON_DEFAULT)

        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = self._UID
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = self._hicon
        nid.szTip = APP_DISPLAY_NAME[:127]
        _shell32_dll.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        self._nid = nid

        msg = wt.MSG()
        while _user32_dll.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            _user32_dll.TranslateMessage(ctypes.byref(msg))
            _user32_dll.DispatchMessageW(ctypes.byref(msg))

    def stop(self) -> None:
        global _active_tray
        self._dismiss_popup()
        if self._nid and self._hwnd:
            _shell32_dll.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))
            self._nid = None
        if self._hicon:
            try:
                _user32_dll.DestroyIcon(self._hicon)
            except Exception:
                pass
            self._hicon = None
        if self._hwnd:
            try:
                _user32_dll.PostMessageW(self._hwnd, WM_DESTROY, 0, 0)
            except Exception:
                pass
            self._hwnd = None
        _active_tray = None

    # ── Icon swapping ────────────────────────────────────────────

    def set_status(self, matching: bool) -> None:
        ico_path = ICON_GREEN if matching else ICON_RED
        new_icon = _load_ico(ico_path)
        if not new_icon:
            return
        old = self._hicon
        self._hicon = new_icon
        if self._nid and self._hwnd:
            self._nid.hIcon = new_icon
            self._nid.uFlags = NIF_ICON
            _shell32_dll.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid))
        if old:
            try:
                _user32_dll.DestroyIcon(old)
            except Exception:
                pass

    # ── Dark‑themed context menu ─────────────────────────────────

    def _show_context_menu(self) -> None:
        """Schedule the themed popup on the tkinter main thread."""
        if self._root:
            self._root.after(0, self._build_popup)

    def _dismiss_popup(self) -> None:
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None

    def _build_popup(self) -> None:
        """Build and show the dark‑themed context menu at cursor position."""
        self._dismiss_popup()

        # Get cursor position
        pt = wt.POINT()
        _user32_dll.GetCursorPos(ctypes.byref(pt))

        popup = tk.Toplevel(self._root)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.configure(bg=_BORDER, highlightthickness=0)
        popup.attributes("-topmost", True)
        popup.attributes("-alpha", 0.97)

        self._popup = popup

        # Inner frame with 1px border effect
        inner = tk.Frame(popup, bg=_BG, padx=2, pady=4)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # ── Header ──
        header = tk.Label(
            inner, text=APP_DISPLAY_NAME,
            bg=_BG, fg=_ACCENT,
            font=(_FONT_FAMILY, _FONT_SIZE - 1, "bold"),
            anchor="w", padx=16, pady=6,
        )
        header.pack(fill="x")

        # Separator after header
        self._add_separator(inner)

        # ── Menu items ──
        toggle_text = "Hide IP Window" if self._overlay_visible else "Show IP Window"
        toggle_icon = "👁" if self._overlay_visible else "👁‍🗨"

        items = [
            ("⚙", "Settings",    self._on_settings,       False),
            (toggle_icon, toggle_text, self._on_toggle_overlay, False),
            ("🔄", "Recheck IP",  self._on_recheck,        False),
            None,  # separator
            ("⏻", "Exit",        self._on_exit,           True),
        ]

        for item in items:
            if item is None:
                self._add_separator(inner)
                continue

            icon_text, label, callback, is_exit = item
            self._add_menu_item(inner, icon_text, label, callback, is_exit)

        # Position & show
        popup.update_idletasks()
        w = popup.winfo_reqwidth()
        h = popup.winfo_reqheight()

        # Position above/below cursor near taskbar
        screen_h = popup.winfo_screenheight()
        x = pt.x - w // 2
        # Keep on screen horizontally
        x = max(4, min(x, popup.winfo_screenwidth() - w - 4))

        if pt.y > screen_h // 2:
            # Cursor near bottom → show above
            y = pt.y - h - 8
        else:
            # Cursor near top → show below
            y = pt.y + 8

        popup.geometry(f"+{x}+{y}")
        popup.deiconify()
        popup.focus_force()

        # Dismiss on focus loss
        popup.bind("<FocusOut>", lambda e: self._dismiss_popup())
        # Also dismiss on Escape
        popup.bind("<Escape>", lambda e: self._dismiss_popup())

    def _add_separator(self, parent: tk.Frame) -> None:
        sep = tk.Frame(parent, bg=_SEPARATOR, height=1)
        sep.pack(fill="x", padx=12, pady=4)

    def _add_menu_item(
        self,
        parent: tk.Frame,
        icon: str,
        text: str,
        callback: Callable | None,
        is_exit: bool = False,
    ) -> None:
        fg = _FG_EXIT if is_exit else _FG
        hover_bg = _BG_EXIT_HOVER if is_exit else _BG_HOVER

        frame = tk.Frame(parent, bg=_BG, cursor="hand2")
        frame.pack(fill="x", padx=4, pady=1)

        # Icon label
        icon_lbl = tk.Label(
            frame, text=icon,
            bg=_BG, fg=_FG_MUTED,
            font=(_FONT_FAMILY, _FONT_SIZE),
            width=2, anchor="center",
        )
        icon_lbl.pack(side="left", padx=(8, 2))

        # Text label
        text_lbl = tk.Label(
            frame, text=text,
            bg=_BG, fg=fg,
            font=(_FONT_FAMILY, _FONT_SIZE),
            anchor="w", padx=4, pady=6,
        )
        text_lbl.pack(side="left", fill="x", expand=True, padx=(0, 16))

        # Hover effects
        def on_enter(e):
            frame.configure(bg=hover_bg)
            icon_lbl.configure(bg=hover_bg)
            text_lbl.configure(bg=hover_bg)

        def on_leave(e):
            frame.configure(bg=_BG)
            icon_lbl.configure(bg=_BG)
            text_lbl.configure(bg=_BG)

        def on_click(e):
            self._dismiss_popup()
            if callback:
                callback()

        for widget in (frame, icon_lbl, text_lbl):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
