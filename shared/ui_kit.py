"""
设计系统：颜色常量 + 通用控件工厂函数
所有 UI 组件都从这里引入颜色和工厂，保证风格统一
"""
import tkinter as tk
from tkinter import ttk

# ── 颜色常量：Midnight Graph UI 紧凑暗色主题 ───────────────────────
THEME_NAME = "midnight_graph_ui"
BUTTON_STYLE = "outline"
FONT_FAMILY = "Microsoft YaHei UI"
RADIUS_PROXY_PAD = 10

BG_BASE     = "#0b0f14"   # 窗口底色
BG_ELEVATED = "#0f151c"   # 顶栏/主要容器
BG_SURFACE  = "#111821"   # 面板/卡片背景
BG_CARD     = "#17212b"   # 输入框/按钮背景
BG_HOVER    = "#22303d"   # 悬停/选中态

BORDER_SUBTLE = "#243241"

FG_PRIMARY = "#e7edf4"   # 主文字
FG_MUTED   = "#9aa7b3"   # 次要文字
FG_DIM     = "#5f6b78"   # 占位符/禁用文字

# 强调色
ACCENT_BLUE   = "#7aa7ff"
ACCENT_GREEN  = "#7dd3b0"
ACCENT_PURPLE = "#b8a6ff"
ACCENT_YELLOW = "#e8c36a"
ACCENT_RED    = "#ff7a90"
ACCENT_CYAN   = "#76d6e8"
ACCENT_ORANGE = "#f0a46a"

DARK_TEXT = "#081016"   # 深色文字（用于亮色按钮上）


# ── 鼠标滚轮绑定 ──────────────────────────────────────────────────
def bind_mousewheel(canvas: tk.Canvas) -> None:
    """将滚轮事件绑定到 canvas，鼠标进入时激活，离开时释放"""
    def _on_enter(_e):
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )
    def _on_leave(_e):
        canvas.unbind_all("<MouseWheel>")
    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)


# ── 通用工厂函数 ─────────────────────────────────────────────────

def make_btn(parent, text: str, command, color: str = ACCENT_BLUE,
             font_size: int = 9, padx: int = 10, pady: int = 4) -> tk.Button:
    """Midnight Graph UI outline button."""
    return tk.Button(
        parent, text=text, command=command,
        bg=BG_CARD, fg=color, relief=tk.FLAT,
        font=(FONT_FAMILY, font_size, "bold"),
        padx=padx, pady=pady,
        activebackground=BG_HOVER, cursor="hand2",
        highlightbackground=color, highlightthickness=1,
    )


def make_panel(parent, bg: str = BG_ELEVATED, padx: int = 10, pady: int = 10) -> tk.Frame:
    """Create a low-contrast floating panel."""
    return tk.Frame(
        parent, bg=bg, padx=padx, pady=pady,
        highlightbackground=BORDER_SUBTLE, highlightthickness=1,
    )


def make_scroll_canvas(parent, bg: str = BG_BASE):
    """
    创建带纵向滚动条的 Canvas + 内部 Frame。
    返回 (canvas, inner_frame)。
    已自动绑定鼠标滚轮和 scrollregion。
    """
    canvas = tk.Canvas(parent, bg=bg, highlightthickness=0)
    sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    inner.bind("<Configure>",
               lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>",
                lambda e: canvas.itemconfig(win_id, width=e.width))
    canvas.configure(yscrollcommand=sb.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    bind_mousewheel(canvas)

    return canvas, inner


class Tooltip:
    """鼠标悬停提示框（深色主题）。用法：Tooltip(widget, "提示文字")"""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 600):
        self._widget = widget
        self._text   = text
        self._delay  = delay          # 毫秒，悬停多久后显示
        self._tw     = None           # Toplevel 气泡窗口
        self._job    = None           # after() 任务 id
        widget.bind("<Enter>",        self._on_enter, add="+")
        widget.bind("<Leave>",        self._on_leave, add="+")
        widget.bind("<ButtonPress>",  self._on_leave, add="+")

    def _on_enter(self, _event=None):
        self._cancel()
        self._job = self._widget.after(self._delay, self._show)

    def _on_leave(self, _event=None):
        self._cancel()
        self._hide()

    def _cancel(self):
        if self._job:
            self._widget.after_cancel(self._job)
            self._job = None

    def _show(self):
        if self._tw:
            return
        x = self._widget.winfo_rootx() + 12
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tw = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(
            tw, text=self._text, justify=tk.LEFT,
            bg=BG_SURFACE, fg=ACCENT_YELLOW,
            relief=tk.FLAT, bd=1,
            font=(FONT_FAMILY, 8),
            padx=10, pady=6,
            wraplength=260,
        )
        label.pack()

    def _hide(self):
        if self._tw:
            self._tw.destroy()
            self._tw = None


def apply_dark_notebook_style() -> None:
    """为 ttk.Notebook 应用深色主题样式（调用一次即可）"""
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Dark.TNotebook", background=BG_BASE, borderwidth=0)
    style.configure(
        "Dark.TNotebook.Tab",
        background=BG_CARD, foreground=FG_PRIMARY,
        padding=[12, 5], font=(FONT_FAMILY, 9),
    )
    style.map(
        "Dark.TNotebook.Tab",
        background=[("selected", BG_HOVER)],
        foreground=[("selected", ACCENT_GREEN)],
    )
