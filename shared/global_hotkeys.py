"""Windows global hotkey registration for app-wide actions."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import itertools
import sys
from typing import Callable

from PySide6.QtGui import QKeySequence


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

_VK_ALIASES = {
    "BACKSPACE": 0x08,
    "BACKTAB": 0x09,
    "TAB": 0x09,
    "RETURN": 0x0D,
    "ENTER": 0x0D,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "SPACE": 0x20,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "END": 0x23,
    "HOME": 0x24,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "INS": 0x2D,
    "INSERT": 0x2D,
    "DEL": 0x2E,
    "DELETE": 0x2E,
    "PLUS": 0xBB,
    "+": 0xBB,
    "COMMA": 0xBC,
    ",": 0xBC,
    "MINUS": 0xBD,
    "-": 0xBD,
    "PERIOD": 0xBE,
    ".": 0xBE,
    "SLASH": 0xBF,
    "/": 0xBF,
    "BACKSLASH": 0xDC,
    "\\": 0xDC,
}

if sys.platform == "win32":
    user32 = ctypes.windll.user32
    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.UnregisterHotKey.restype = wintypes.BOOL
    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = ctypes.c_ssize_t
    user32.RegisterClassW.argtypes = [ctypes.c_void_p]
    user32.RegisterClassW.restype = wintypes.ATOM
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.HWND,
        wintypes.HANDLE,
        wintypes.HINSTANCE,
        wintypes.LPVOID,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND
else:
    user32 = None


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


if sys.platform == "win32":
    WNDPROC = ctypes.WINFUNCTYPE(
        ctypes.c_ssize_t,
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )
else:
    WNDPROC = None


class GlobalHotkeyManager:
    """Registers process-level Windows hotkeys and dispatches WM_HOTKEY."""

    def __init__(self):
        self._callbacks: dict[int, Callable[[], None]] = {}
        self._registered: set[int] = set()
        self._ids = itertools.count(0x5100)
        self._hwnd: int | None = None
        self._wndproc = None

    @property
    def supported(self) -> bool:
        return user32 is not None

    def register(self, sequence: str, callback: Callable[[], None]) -> int | None:
        parsed = parse_hotkey(sequence)
        if not self.supported or parsed is None:
            return None
        hwnd = self._ensure_message_window()
        if not hwnd:
            return None
        modifiers, vk = parsed
        hotkey_id = next(self._ids)
        if not user32.RegisterHotKey(hwnd, hotkey_id, modifiers | MOD_NOREPEAT, vk):
            return None
        self._registered.add(hotkey_id)
        self._callbacks[hotkey_id] = callback
        return hotkey_id

    def unregister(self, hotkey_id: int | None) -> None:
        if hotkey_id is None or hotkey_id not in self._registered:
            return
        if self.supported and self._hwnd:
            user32.UnregisterHotKey(self._hwnd, hotkey_id)
        self._registered.discard(hotkey_id)
        self._callbacks.pop(hotkey_id, None)

    def unregister_all(self) -> None:
        for hotkey_id in list(self._registered):
            self.unregister(hotkey_id)

    def _ensure_message_window(self) -> int | None:
        if self._hwnd or not self.supported or WNDPROC is None:
            return self._hwnd
        hinstance = ctypes.windll.kernel32.GetModuleHandleW(None)
        class_name = "PromptToolGlobalHotkeyWindow"
        self._wndproc = WNDPROC(self._window_proc)
        wndclass = WNDCLASS()
        wndclass.lpfnWndProc = self._wndproc
        wndclass.hInstance = hinstance
        wndclass.lpszClassName = class_name
        user32.RegisterClassW(ctypes.byref(wndclass))
        self._hwnd = user32.CreateWindowExW(
            0,
            class_name,
            "PromptToolHotkeys",
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            hinstance,
            None,
        )
        return self._hwnd or None

    def _window_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_HOTKEY:
            callback = self._callbacks.get(int(wparam))
            if callback:
                callback()
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC if WNDPROC is not None else ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


def normalize_hotkey(sequence: str) -> str:
    raw = (sequence or "").strip()
    if not raw:
        return ""
    return QKeySequence(raw).toString(QKeySequence.PortableText) or ""


def parse_hotkey(sequence: str) -> tuple[int, int] | None:
    normalized = normalize_hotkey(sequence)
    if not normalized:
        return None
    parts = [part.strip() for part in normalized.split("+") if part.strip()]
    if not parts:
        return None
    key = parts[-1]
    modifiers = 0
    for part in parts[:-1]:
        name = part.lower()
        if name == "ctrl":
            modifiers |= MOD_CONTROL
        elif name == "alt":
            modifiers |= MOD_ALT
        elif name == "shift":
            modifiers |= MOD_SHIFT
        elif name in ("meta", "win"):
            modifiers |= MOD_WIN
        else:
            return None
    vk = key_to_vk(key)
    if vk is None:
        return None
    return modifiers, vk


def key_to_vk(key: str) -> int | None:
    name = key.strip().upper()
    if len(name) == 1 and ("A" <= name <= "Z" or "0" <= name <= "9"):
        return ord(name)
    if name.startswith("F") and name[1:].isdigit():
        num = int(name[1:])
        if 1 <= num <= 24:
            return 0x70 + num - 1
    return _VK_ALIASES.get(name)


global_hotkeys = GlobalHotkeyManager()
