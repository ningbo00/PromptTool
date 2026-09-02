"""
设计系统：颜色常量 + 通用控件工厂函数
所有 UI 组件都从这里引入颜色和工厂，保证风格统一
"""
from shared import qt_compat as tk
from shared.qt_compat import ttk
from PySide6.QtWidgets import QApplication, QSizePolicy, QToolTip

# ── 颜色常量：VS Code inspired restrained dark theme ───────────────
THEME_NAME = "midnight_graph_ui"
BUTTON_STYLE = "outline"
FONT_FAMILY = "Microsoft YaHei UI"
RADIUS_PROXY_PAD = 10

BG_BASE     = "#181818"   # 窗口底色
BG_ELEVATED = "#1f1f1f"   # 顶栏/主要容器
BG_SURFACE  = "#242424"   # 面板/卡片背景
BG_CARD     = "#2d2d2d"   # 输入框/按钮背景
BG_HOVER    = "#333333"   # 悬停/选中态

BORDER_SUBTLE = "#3a3a3a"

FG_PRIMARY = "#e6e6e6"   # 主文字
FG_MUTED   = "#a0a0a0"   # 次要文字
FG_DIM     = "#6f6f6f"   # 占位符/禁用文字

# 只保留蓝色作为主强调色，其余语义色全部降为灰色。
ACCENT_BLUE   = "#3794ff"
ACCENT_GREEN  = FG_MUTED
ACCENT_PURPLE = FG_MUTED
ACCENT_YELLOW = FG_MUTED
ACCENT_RED    = FG_MUTED
ACCENT_CYAN   = FG_MUTED
ACCENT_ORANGE = FG_MUTED

DARK_TEXT = "#ffffff"   # 蓝色填充按钮上的文字


def apply_app_theme() -> None:
    """Apply the shared Qt stylesheet for the reference-image dark design."""
    app = QApplication.instance()
    if app is None:
        return
    app.setStyleSheet(f"""
        QWidget {{
            background: {BG_BASE};
            color: {FG_PRIMARY};
            font-family: "{FONT_FAMILY}";
            font-size: 9pt;
        }}
        QDialog, QWidget#Tk, QWidget#Toplevel {{
            background: {BG_BASE};
        }}
        QPushButton {{
            background: {BG_CARD};
            color: {FG_PRIMARY};
            border: 1px solid #343434;
            border-radius: 9px;
            min-height: 28px;
            padding: 4px 10px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            background: {BG_HOVER};
            border-color: #4a4a4a;
        }}
        QPushButton:pressed {{
            background: #3a3a3a;
        }}
        QPushButton:disabled {{
            color: {FG_DIM};
            background: #252525;
            border-color: #303030;
        }}
        QLineEdit, QTextEdit, QComboBox {{
            background: {BG_CARD};
            color: {FG_PRIMARY};
            border: 1px solid #343434;
            border-radius: 9px;
            min-height: 30px;
            padding: 4px 9px;
            selection-background-color: {ACCENT_BLUE};
        }}
        QTextEdit {{
            padding: 10px;
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border-color: {ACCENT_BLUE};
        }}
        QTextEdit:disabled, QLineEdit:disabled {{
            color: {FG_MUTED};
            background: {BG_SURFACE};
        }}
        QTabWidget::pane {{
            border: 1px solid #343434;
            border-radius: 10px;
            background: {BG_SURFACE};
            top: -1px;
        }}
        QTabBar::tab {{
            background: {BG_CARD};
            color: {FG_MUTED};
            border: 1px solid #343434;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            min-height: 26px;
            padding: 5px 12px;
            margin-right: 3px;
        }}
        QTabBar::tab:selected {{
            background: {BG_HOVER};
            color: {ACCENT_BLUE};
            border-color: {ACCENT_BLUE};
        }}
        QScrollBar:vertical {{
            width: 10px;
            background: transparent;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: #2d3946;
            border-radius: 5px;
            min-height: 28px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {ACCENT_BLUE};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollArea, QScrollArea:focus, QScrollArea QWidget {{
            border: none;
            outline: 0;
        }}
        QCheckBox, QRadioButton {{
            color: {FG_MUTED};
            spacing: 7px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 15px;
            height: 15px;
        }}
        QSplitter::handle {{
            background: {BORDER_SUBTLE};
            width: 1px;
        }}
        QToolTip {{
            background: {BG_SURFACE};
            color: {FG_PRIMARY};
            border: 1px solid {BORDER_SUBTLE};
            border-radius: 6px;
            padding: 6px 8px;
        }}
    """)


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
    创建带纵向滚动条的 Qt ScrollArea + 内部 Frame。
    返回 (scroll_area, inner_frame)，保留旧调用名以减少业务代码改动。
    """
    scroll_area = tk.ScrollArea(parent, bg=bg, highlightthickness=0)
    inner = tk.Frame(scroll_area, bg=bg)
    scroll_area.set_widget(inner)
    scroll_area.pack(fill=tk.BOTH, expand=True)
    bind_mousewheel(scroll_area)
    return scroll_area, inner


def brick_text_score(text: str) -> int:
    """Estimate visual width; CJK characters count wider than ASCII."""
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    if not lines:
        return 0
    return max(sum(2 if ord(ch) > 127 else 1 for ch in line) for line in lines)


def brick_span(text: str, *, min_units: int = 3, max_units: int = 6) -> int:
    """Return a 12-column span so short chips stay compact and long chips get room."""
    score = brick_text_score(text)
    if score <= 14:
        span = min_units
    elif score <= 22:
        span = min_units + 1
    elif score <= 32:
        span = min_units + 2
    else:
        span = min_units + 3
    return max(min_units, min(max_units, span))


def prepare_brick_grid(frame, total_units: int = 12, spacing: int = 6) -> None:
    """Configure a frame as a dense proportional brick grid."""
    for col in range(total_units):
        frame.grid_columnconfigure(col, weight=1)
    if hasattr(frame, "_ensure_grid_layout"):
        layout = frame._ensure_grid_layout()
        layout.setHorizontalSpacing(spacing)
        layout.setVerticalSpacing(spacing)


def place_brick(widget, row: int, col: int, span: int, *,
                total_units: int = 12, padx: int = 0, pady: int = 0) -> tuple[int, int]:
    """Place a widget in the next available brick slot and return the next cursor."""
    span = max(1, min(total_units, int(span)))
    if col and col + span > total_units:
        row += 1
        col = 0
    widget.grid(row=row, column=col, columnspan=span, sticky="ew", padx=padx, pady=pady)
    height = getattr(widget, "_brick_height", None)
    if height and hasattr(widget, "setMinimumHeight"):
        widget.setFixedHeight(int(height))
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    col += span
    if col >= total_units:
        return row + 1, 0
    return row, col


def make_chip_button(widget, height: int = 38):
    """Apply compact fixed-height chip styling after legacy button creation."""
    widget._is_chip_button = True
    widget._brick_height = int(height)
    if hasattr(widget, "_apply_style"):
        widget._apply_style()
    widget.setFixedHeight(int(height))
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return widget


class Tooltip:
    """Qt-native tooltip wrapper. Avoids flashing helper Toplevel windows."""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 600):
        self._widget = widget
        self._text   = text
        self._delay  = delay          # 毫秒，悬停多久后显示
        self._tw     = None           # kept for compatibility with old call sites
        self._job    = None           # after() 任务 id
        if hasattr(widget, "setToolTip"):
            widget.setToolTip(text)
        if hasattr(widget, "setToolTipDuration"):
            widget.setToolTipDuration(12000)

    def _on_enter(self, _event=None):
        return None

    def _on_leave(self, _event=None):
        QToolTip.hideText()

    def _cancel(self):
        self._job = None

    def _show(self):
        return None

    def _hide(self):
        QToolTip.hideText()


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
