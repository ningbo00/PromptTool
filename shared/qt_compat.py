"""Tk-like compatibility facade backed by PySide6.

The original UI was written for tkinter. This module provides the subset of
that API used by the app while rendering with Qt/PySide6, so feature logic can
be preserved during the UI migration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
import re
import sys

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QPainter, QPen, QBrush, QTextCursor, QTextOption
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QScrollBar,
    QSizePolicy,
    QSlider,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

LEFT = "left"
RIGHT = "right"
TOP = "top"
BOTTOM = "bottom"
BOTH = "both"
X = "x"
Y = "y"
HORIZONTAL = "horizontal"
VERTICAL = "vertical"
WORD = "word"
END = "end"
NORMAL = "normal"
DISABLED = "disabled"
FLAT = "flat"
CENTER = "center"


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
        app.setStyle("Fusion")
    return app


def _parent_widget(parent: Any) -> QWidget | None:
    return parent if isinstance(parent, QWidget) else None


def _font(value: Any) -> QFont | None:
    if not value:
        return None
    if isinstance(value, QFont):
        return value
    if isinstance(value, (tuple, list)):
        family = str(value[0]) if value else "Microsoft YaHei UI"
        size = int(value[1]) if len(value) > 1 and str(value[1]).lstrip("-").isdigit() else 9
        font = QFont(family, size)
        flags = {str(v).lower() for v in value[2:]}
        font.setBold("bold" in flags)
        font.setItalic("italic" in flags)
        font.setStrikeOut("overstrike" in flags)
        return font
    return QFont(str(value))


def _parse_geometry(value: str) -> tuple[int | None, int | None, int | None, int | None]:
    match = re.match(r"(?:(\d+)x(\d+))?(?:\+(-?\d+)\+(-?\d+))?", value or "")
    if not match:
        return None, None, None, None
    width, height, x, y = match.groups()
    return (
        int(width) if width else None,
        int(height) if height else None,
        int(x) if x else None,
        int(y) if y else None,
    )


@dataclass
class Event:
    x: int = 0
    y: int = 0
    x_root: int = 0
    y_root: int = 0
    delta: int = 0
    width: int = 0
    height: int = 0


class Variable:
    def __init__(self, value: Any = None):
        self._value = value
        self._callbacks: list[Callable[..., Any]] = []
        self._widgets: list[Any] = []

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        for widget in list(self._widgets):
            if hasattr(widget, "_sync_from_variable"):
                widget._sync_from_variable()
        for callback in list(self._callbacks):
            callback(None, None, None)

    def trace_add(self, _mode: str, callback: Callable[..., Any]):
        self._callbacks.append(callback)
        return str(id(callback))

    def _bind_widget(self, widget: Any):
        if widget not in self._widgets:
            self._widgets.append(widget)


class StringVar(Variable):
    def __init__(self, value: str = ""):
        super().__init__(value)


class BooleanVar(Variable):
    def __init__(self, value: bool = False):
        super().__init__(bool(value))

    def set(self, value):
        super().set(bool(value))


class IntVar(Variable):
    def __init__(self, value: int = 0):
        super().__init__(int(value))

    def set(self, value):
        super().set(int(float(value)))


class DoubleVar(Variable):
    def __init__(self, value: float = 0.0):
        super().__init__(float(value))

    def set(self, value):
        super().set(float(value))


class TkWidgetMixin:
    def _tk_init(self, **kwargs):
        self._pack_layout: QHBoxLayout | QVBoxLayout | None = None
        self._pack_orientation: str | None = None
        self._grid_layout: QGridLayout | None = None
        self._bindings: dict[str, list[Callable[[Event], Any]]] = {}
        self._destroyed = False
        self._bg = None
        self._fg = None
        self._anchor = None
        self._last_style_sheet = ""
        self._style_bits: dict[str, Any] = {}
        self.installEventFilter(self)
        self.setObjectName(self.__class__.__name__)
        if kwargs:
            self.config(**kwargs)

    def _ensure_pack_layout(self, side: str | None = None):
        desired = "h" if side in (LEFT, RIGHT) else "v"
        if self._pack_layout is not None:
            return self._pack_layout
        layout = QHBoxLayout() if desired == "h" else QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        if desired == "v":
            layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)
        self._pack_layout = layout
        self._pack_orientation = desired
        return layout

    def _ensure_grid_layout(self):
        if self._grid_layout is not None:
            return self._grid_layout
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.setLayout(layout)
        self._grid_layout = layout
        return layout

    def pack(self, side: str | None = None, fill: str | None = None, expand: bool = False,
             padx: Any = 0, pady: Any = 0, anchor: str | None = None, **_kwargs):
        parent = self.parentWidget()
        if parent is None:
            if self.isWindow():
                self.show()
            return
        if isinstance(parent, (QTabWidget, QSplitter)):
            return
        if not hasattr(parent, "_ensure_pack_layout"):
            return
        layout = parent._ensure_pack_layout(side)
        margins = _margins(padx, pady)
        if margins != (0, 0, 0, 0):
            self.setContentsMargins(*margins)
        _apply_size_policy(self, fill, expand)
        if side == RIGHT and isinstance(layout, QHBoxLayout):
            layout.addStretch(1)
        layout.addWidget(self, 1 if expand else 0, _alignment(anchor))
        self.show()

    def pack_forget(self):
        parent = self.parentWidget()
        if parent is not None and parent.layout() is not None:
            parent.layout().removeWidget(self)
        self.hide()

    def grid(self, row: int = 0, column: int = 0, sticky: str = "", padx: Any = 0,
             pady: Any = 0, columnspan: int = 1, rowspan: int = 1, **_kwargs):
        parent = self.parentWidget()
        if parent is None or not hasattr(parent, "_ensure_grid_layout"):
            return
        layout = parent._ensure_grid_layout()
        margins = _margins(padx, pady)
        if margins != (0, 0, 0, 0):
            self.setContentsMargins(*margins)
        if sticky:
            h_fill = "w" in sticky and "e" in sticky
            v_fill = "n" in sticky and "s" in sticky
            _apply_size_policy(self, BOTH if h_fill and v_fill else X if h_fill else Y if v_fill else None, False)
        layout.addWidget(self, row, column, rowspan, columnspan, _sticky_alignment(sticky))
        self.show()

    def grid_columnconfigure(self, index: int, weight: int = 0, minsize: int = 0, **_kwargs):
        layout = self._ensure_grid_layout()
        layout.setColumnStretch(index, weight)
        if minsize:
            layout.setColumnMinimumWidth(index, minsize)

    def grid_rowconfigure(self, index: int, weight: int = 0, minsize: int = 0, **_kwargs):
        layout = self._ensure_grid_layout()
        layout.setRowStretch(index, weight)
        if minsize:
            layout.setRowMinimumHeight(index, minsize)

    def bind(self, sequence: str, callback: Callable[[Event], Any], add: str | None = None):
        if add:
            self._bindings.setdefault(sequence, []).append(callback)
        else:
            self._bindings[sequence] = [callback]

    def bind_all(self, sequence: str, callback: Callable[[Event], Any]):
        self.bind(sequence, callback, add="+")

    def unbind_all(self, sequence: str):
        self._bindings.pop(sequence, None)

    def eventFilter(self, _obj, event):
        sequence = None
        ev = Event()
        et = event.type()
        if et == QEvent.Enter:
            sequence = "<Enter>"
        elif et == QEvent.Leave:
            sequence = "<Leave>"
        elif et == QEvent.FocusIn:
            sequence = "<FocusIn>"
        elif et == QEvent.FocusOut:
            sequence = "<FocusOut>"
        elif et == QEvent.Resize:
            sequence = "<Configure>"
            ev.width = self.width()
            ev.height = self.height()
        elif et == QEvent.MouseButtonPress:
            sequence = "<Button-3>" if event.button() == Qt.RightButton else "<Button-1>"
            pos = event.position().toPoint()
            gpos = event.globalPosition().toPoint()
            ev = Event(pos.x(), pos.y(), gpos.x(), gpos.y())
        elif et == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
            sequence = "<B1-Motion>"
            pos = event.position().toPoint()
            gpos = event.globalPosition().toPoint()
            ev = Event(pos.x(), pos.y(), gpos.x(), gpos.y())
        elif et == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            sequence = "<ButtonRelease-1>"
            pos = event.position().toPoint()
            gpos = event.globalPosition().toPoint()
            ev = Event(pos.x(), pos.y(), gpos.x(), gpos.y())
        elif et == QEvent.Wheel:
            sequence = "<MouseWheel>"
            pos = event.position().toPoint()
            gpos = event.globalPosition().toPoint()
            ev = Event(pos.x(), pos.y(), gpos.x(), gpos.y(), delta=event.angleDelta().y())
        elif et == QEvent.KeyRelease:
            sequence = "<KeyRelease>"
        if sequence and sequence in self._bindings:
            for callback in list(self._bindings[sequence]):
                callback(ev)
        return False

    def config(self, **kwargs):
        self.configure(**kwargs)

    def configure(self, **kwargs):
        state = kwargs.pop("state", None)
        if state is not None:
            self.setEnabled(state != DISABLED)
            if isinstance(self, Text):
                self.setReadOnly(state == DISABLED)
        text = kwargs.pop("text", None)
        if text is not None and hasattr(self, "setText"):
            self.setText(str(text))
        font = _font(kwargs.pop("font", None))
        if font is not None:
            self.setFont(font)
        width = kwargs.pop("width", None)
        height = kwargs.pop("height", None)
        if isinstance(width, int):
            self.setMinimumWidth(max(1, width) * 8)
        if isinstance(height, int):
            self.setMinimumHeight(max(1, height) * 18)
        bg = kwargs.pop("bg", kwargs.pop("background", None))
        fg = kwargs.pop("fg", kwargs.pop("foreground", None))
        if bg is not None:
            self._bg = str(bg)
        if fg is not None:
            self._fg = str(fg)
        if "highlightbackground" in kwargs:
            self._style_bits["border"] = kwargs.pop("highlightbackground")
        if "highlightthickness" in kwargs:
            self._style_bits["border_width"] = kwargs.pop("highlightthickness")
        if "selectcolor" in kwargs:
            self._style_bits["select"] = kwargs.pop("selectcolor")
        cursor = kwargs.pop("cursor", None)
        if cursor:
            self.setCursor(Qt.PointingHandCursor if cursor == "hand2" else Qt.CrossCursor if cursor == "crosshair" else Qt.ArrowCursor)
        wraplength = kwargs.pop("wraplength", None)
        if wraplength and isinstance(self, QLabel):
            self.setWordWrap(True)
            self.setMaximumWidth(int(wraplength) + 20)
        justify = kwargs.pop("justify", None)
        if justify and isinstance(self, QLabel):
            self.setAlignment(Qt.AlignLeft if justify == LEFT else Qt.AlignCenter)
        anchor = kwargs.pop("anchor", None)
        if anchor:
            self._anchor = anchor
            if isinstance(self, QLabel):
                self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter if anchor == "w" else Qt.AlignCenter)
        padx = kwargs.pop("padx", None)
        pady = kwargs.pop("pady", None)
        if padx is not None or pady is not None:
            self.setContentsMargins(int(padx or 0), int(pady or 0), int(padx or 0), int(pady or 0))
        for ignored in (
            "activebackground", "activeforeground", "insertbackground", "relief",
            "bd", "borderwidth", "showvalue", "troughcolor", "resolution",
        ):
            kwargs.pop(ignored, None)
        self._apply_style()

    def _apply_style(self):
        parts = []
        if self._bg:
            parts.append(f"background-color: {self._bg};")
        if self._fg:
            parts.append(f"color: {self._fg};")
        if isinstance(self, (QFrame, QPushButton, QLineEdit, QTextEdit, QComboBox)):
            radius = 14 if isinstance(self, QFrame) else 10
            border = self._style_bits.get("border", "#343434")
            border_width = int(self._style_bits.get("border_width", 0) or 0)
            parts.append(f"border-radius: {radius}px;")
            parts.append(f"border: {border_width}px solid {border};" if border_width else "border: none;")
        if isinstance(self, QPushButton):
            if getattr(self, "_is_toolbar_square", False):
                parts.append("min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px; padding: 4px;")
            elif getattr(self, "_is_primary_action", False):
                parts.append(
                    "min-height: 30px; max-height: 30px; padding: 0px 8px; "
                    "background-color: #1f2933; border: 1px solid #3794ff; color: #ffffff;"
                )
            elif getattr(self, "_is_primary_dropdown", False):
                parts.append(
                    "min-width: 28px; max-width: 28px; min-height: 30px; max-height: 30px; "
                    "padding: 0px; background-color: #1f2933; border: 1px solid #3794ff; color: #ffffff;"
                )
            elif getattr(self, "_is_compact_restore", False):
                parts.append("min-width: 50px; max-width: 50px; min-height: 22px; max-height: 22px; padding: 0px;")
            elif getattr(self, "_is_ai_action_button", False):
                parts.append("min-height: 20px; max-height: 22px; padding: 0px 4px;")
            elif getattr(self, "_is_chip_button", False):
                parts.append("min-height: 30px; padding: 2px 6px;")
            else:
                parts.append("min-height: 28px; padding: 4px 10px;")
            if self._anchor == "w":
                parts.append("text-align: left;")
        if isinstance(self, (QLineEdit, QComboBox)):
            parts.append("min-height: 30px; padding: 4px 9px;")
        if isinstance(self, (QLineEdit, QTextEdit)):
            parts.append("selection-background-color: #3794ff;")
        if isinstance(self, QTextEdit):
            parts.append("padding: 10px;")
        if parts:
            style_sheet = " ".join(parts)
            if style_sheet != self._last_style_sheet:
                self._last_style_sheet = style_sheet
                self.setStyleSheet(style_sheet)

    def cget(self, key: str):
        if key in ("bg", "background"):
            return self._bg or ""
        if key in ("fg", "foreground"):
            return self._fg or ""
        if key == "text" and hasattr(self, "text"):
            return self.text()
        return ""

    def winfo_children(self):
        return [child for child in self.findChildren(QWidget, options=Qt.FindDirectChildrenOnly)]

    def winfo_exists(self):
        return not self._destroyed

    def winfo_width(self):
        return self.width()

    def winfo_height(self):
        return self.height()

    def winfo_x(self):
        return self.x()

    def winfo_y(self):
        return self.y()

    def winfo_rootx(self):
        return self.mapToGlobal(QPoint(0, 0)).x()

    def winfo_rooty(self):
        return self.mapToGlobal(QPoint(0, 0)).y()

    def after(self, delay_ms: int, callback: Callable[..., Any]):
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        timer.start(delay_ms)
        return timer

    def after_cancel(self, timer):
        if timer:
            timer.stop()

    def destroy(self):
        self._destroyed = True
        self.hide()
        parent = self.parentWidget()
        if parent is not None and parent.layout() is not None:
            parent.layout().removeWidget(self)
        if self.isWindow():
            self.close()
        self.deleteLater()

    def focus_set(self):
        self.setFocus()


class Tk(TkWidgetMixin, QWidget):
    def __init__(self, *_, **kwargs):
        _app()
        super().__init__(None)
        self._tk_init(**kwargs)

    def title(self, text: str):
        self.setWindowTitle(str(text))

    def geometry(self, value: str):
        w, h, x, y = _parse_geometry(value)
        if w and h:
            self.resize(w, h)
        if x is not None and y is not None:
            self.move(x, y)

    def minsize(self, w: int, h: int):
        self.setMinimumSize(w, h)

    def resizable(self, *_args):
        return None

    def mainloop(self):
        self.show()
        return _app().exec()

    def withdraw(self):
        self.hide()

    def deiconify(self):
        self.showNormal()
        self.raise_()

    def attributes(self, attr: str, value: Any = None):
        if attr == "-topmost" and value is not None:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(value))
            self.show()

    def update_idletasks(self):
        _app().processEvents()


class Toplevel(TkWidgetMixin, QDialog):
    def __init__(self, parent=None, **kwargs):
        _app()
        super().__init__(_parent_widget(parent))
        self._tk_init(**kwargs)

    def title(self, text: str):
        self.setWindowTitle(str(text))

    def geometry(self, value: str):
        w, h, x, y = _parse_geometry(value)
        if w and h:
            self.resize(w, h)
        if x is not None and y is not None:
            self.move(x, y)
        self._schedule_initial_show()

    def minsize(self, w: int, h: int):
        self.setMinimumSize(w, h)

    def resizable(self, *_args):
        return None

    def grab_set(self):
        self.setWindowModality(Qt.ApplicationModal)
        self._schedule_initial_show()

    def withdraw(self):
        self.hide()

    def deiconify(self):
        self.showNormal()
        self.raise_()

    def update_idletasks(self):
        _app().processEvents()

    def overrideredirect(self, enabled: bool):
        self.setWindowFlag(Qt.FramelessWindowHint, bool(enabled))
        if self.isVisible():
            self.show()

    def wm_overrideredirect(self, enabled: bool):
        self.overrideredirect(enabled)

    def wm_geometry(self, value: str):
        self.geometry(value)

    def attributes(self, attr: str, value: Any = None):
        if attr == "-topmost" and value is not None:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(value))
            if self.isVisible():
                self.show()

    def _schedule_initial_show(self):
        if self.isVisible() or self._destroyed:
            return

        def _show_if_alive():
            if not self._destroyed and not self.isVisible():
                self.show()

        QTimer.singleShot(0, _show_if_alive)


class Frame(TkWidgetMixin, QFrame):
    def __init__(self, parent=None, **kwargs):
        super().__init__(_parent_widget(parent))
        self._tk_init(**kwargs)


class Label(TkWidgetMixin, QLabel):
    def __init__(self, parent=None, text: str = "", **kwargs):
        super().__init__(str(text), _parent_widget(parent))
        self._tk_init(**kwargs)


class Button(TkWidgetMixin, QPushButton):
    def __init__(self, parent=None, text: str = "", command: Callable[..., Any] | None = None, **kwargs):
        super().__init__(str(text), _parent_widget(parent))
        self.setFocusPolicy(Qt.NoFocus)
        self.command = command
        if command:
            self.clicked.connect(lambda _checked=False, cmd=command: cmd())
        self._tk_init(**kwargs)

    def invoke(self):
        if self.command:
            self.command()


class Entry(TkWidgetMixin, QLineEdit):
    def __init__(self, parent=None, textvariable: Variable | None = None, show: str | None = None, **kwargs):
        super().__init__(_parent_widget(parent))
        self._var = textvariable
        if show == "*":
            self.setEchoMode(QLineEdit.Password)
        if self._var:
            self._var._bind_widget(self)
            self.setText(str(self._var.get()))
            self.textChanged.connect(lambda text: self._var.set(text) if self._var.get() != text else None)
        self._tk_init(**kwargs)

    def _sync_from_variable(self):
        value = str(self._var.get()) if self._var else ""
        if self.text() != value:
            self.setText(value)

    def get(self):
        return self.text()

    def delete(self, _start=0, _end=None):
        self.clear()

    def insert(self, index, text):
        self.setText(str(text) + self.text() if index in (0, "0") else self.text() + str(text))

    def select_range(self, start, end):
        self.setSelection(int(start), len(self.text()) if end == END else int(end) - int(start))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyRelease and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            for callback in self._bindings.get("<Return>", []):
                callback(Event())
        return super().eventFilter(obj, event)


class Text(TkWidgetMixin, QTextEdit):
    def __init__(self, parent=None, wrap: Any = None, **kwargs):
        super().__init__(_parent_widget(parent))
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self._tk_init(**kwargs)

    def get(self, _start="1.0", end=END):
        text = self.toPlainText()
        return text + "\n" if end == END else text

    def delete(self, _start="1.0", _end=END):
        self.clear()

    def insert(self, index, text, _tag=None):
        if index in ("1.0", 0, "0") and not self.toPlainText():
            self.setPlainText(str(text))
        else:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            self.insertPlainText(str(text))

    def tag_config(self, *_args, **_kwargs):
        return None

    def yview(self, *_args):
        if not _args:
            return None
        bar = self.verticalScrollBar()
        if _args[0] == "moveto" and len(_args) > 1:
            bar.setValue(int(float(_args[1]) * bar.maximum()))
        elif _args[0] == "scroll" and len(_args) > 1:
            bar.setValue(bar.value() + int(_args[1]) * 36)
        return None

    def configure(self, **kwargs):
        kwargs.pop("yscrollcommand", None)
        super().configure(**kwargs)

    def see(self, *_args):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class Checkbutton(TkWidgetMixin, QCheckBox):
    def __init__(self, parent=None, text: str = "", variable: Variable | None = None,
                 command: Callable[..., Any] | None = None, **kwargs):
        super().__init__(str(text), _parent_widget(parent))
        self.setFocusPolicy(Qt.NoFocus)
        self._var = variable
        self.command = command
        if self._var:
            self._var._bind_widget(self)
            self.setChecked(bool(self._var.get()))
        self.toggled.connect(self._on_toggled)
        self._tk_init(**kwargs)

    def _on_toggled(self, value: bool):
        if self._var and self._var.get() != value:
            self._var.set(value)
        if self.command:
            self.command()

    def _sync_from_variable(self):
        if self._var and self.isChecked() != bool(self._var.get()):
            self.setChecked(bool(self._var.get()))


class Radiobutton(TkWidgetMixin, QRadioButton):
    def __init__(self, parent=None, text: str = "", variable: Variable | None = None,
                 value: Any = None, command: Callable[..., Any] | None = None, **kwargs):
        super().__init__(str(text), _parent_widget(parent))
        self.setFocusPolicy(Qt.NoFocus)
        self._var = variable
        self._value = value
        self.command = command
        if self._var:
            self._var._bind_widget(self)
            self.setChecked(self._var.get() == self._value)
        self.toggled.connect(self._on_toggled)
        self._tk_init(**kwargs)

    def _on_toggled(self, checked: bool):
        if checked:
            if self._var and self._var.get() != self._value:
                self._var.set(self._value)
            if self.command:
                self.command()

    def _sync_from_variable(self):
        if self._var:
            self.setChecked(self._var.get() == self._value)


class Menubutton(Button):
    def config(self, **kwargs):
        menu = kwargs.pop("menu", None)
        if menu is not None:
            self.setMenu(menu)
        super().config(**kwargs)


class Menu(QMenu):
    def __init__(self, parent=None, tearoff: int = 0, **kwargs):
        super().__init__(_parent_widget(parent))
        self._bg = None
        self._fg = None
        self.config(**kwargs)

    def add_command(self, label: str, command: Callable[..., Any] | None = None, **kwargs):
        action = QAction(label, self)
        if kwargs.get("state") == DISABLED:
            action.setEnabled(False)
        if command:
            action.triggered.connect(lambda _checked=False, cmd=command: cmd())
        self.addAction(action)

    def add_separator(self):
        self.addSeparator()

    def tk_popup(self, x_root: int, y_root: int):
        self.exec(QPoint(x_root, y_root))

    def config(self, **kwargs):
        bg = kwargs.pop("bg", None)
        fg = kwargs.pop("fg", None)
        if bg:
            self._bg = bg
        if fg:
            self._fg = fg
        if self._bg or self._fg:
            self.setStyleSheet(
                f"QMenu {{ background: {self._bg or '#1f1f1f'}; color: {self._fg or '#e6e6e6'}; "
                "border: 1px solid #343434; }} QMenu::item:selected { background: #333333; }"
            )


class Canvas(TkWidgetMixin, QGraphicsView):
    def __init__(self, parent=None, width: int | None = None, height: int | None = None, **kwargs):
        super().__init__(_parent_widget(parent))
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setFrameShape(QFrame.NoFrame)
        self.setRenderHint(QPainter.Antialiasing, True)
        if width:
            self.setMinimumWidth(width)
        if height:
            self.setMinimumHeight(height)
        if width and height:
            self.setSceneRect(0, 0, width, height)
        self._tk_init(**kwargs)

    def create_window(self, xy, window=None, anchor=None):
        if window is None:
            return None
        proxy = self._scene.addWidget(window)
        proxy.setPos(float(xy[0]), float(xy[1]))
        window.show()
        return proxy

    def create_oval(self, x1, y1, x2, y2, outline="", fill="", width=1, tags=None):
        item = QGraphicsEllipseItem(float(x1), float(y1), float(x2) - float(x1), float(y2) - float(y1))
        item.setPen(QPen(QColor(outline), width) if outline else QPen(Qt.NoPen))
        item.setBrush(QBrush(QColor(fill)) if fill else QBrush(Qt.NoBrush))
        self._scene.addItem(item)
        return item

    def create_line(self, *args, fill="#ffffff", width=1, dash=None, smooth=False):
        points = args[0] if len(args) == 1 and isinstance(args[0], list) else list(args)
        pen = QPen(QColor(fill), width)
        if dash:
            pen.setStyle(Qt.DashLine)
        last = None
        for i in range(0, len(points) - 2, 2):
            last = QGraphicsLineItem(float(points[i]), float(points[i + 1]), float(points[i + 2]), float(points[i + 3]))
            last.setPen(pen)
            self._scene.addItem(last)
        return last

    def delete(self, target):
        if target == "all":
            self._scene.clear()

    def itemconfig(self, item, **kwargs):
        if hasattr(item, "resize") and "width" in kwargs:
            item.resize(float(kwargs["width"]), item.size().height())

    def bbox(self, *_args):
        rect = self._scene.itemsBoundingRect()
        return (rect.left(), rect.top(), rect.right(), rect.bottom())

    def yview(self, *_args):
        if _args:
            bar = self.verticalScrollBar()
            if _args[0] == "moveto" and len(_args) > 1:
                bar.setValue(int(float(_args[1]) * bar.maximum()))
            elif _args[0] == "scroll" and len(_args) > 1:
                bar.setValue(bar.value() + int(_args[1]) * 36)
        return None

    def yview_scroll(self, number: int, _units: str):
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + number * 24)

    def configure(self, **kwargs):
        kwargs.pop("yscrollcommand", None)
        kwargs.pop("scrollregion", None)
        super().configure(**kwargs)


class ScrollArea(TkWidgetMixin, QScrollArea):
    def __init__(self, parent=None, **kwargs):
        super().__init__(_parent_widget(parent))
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.viewport().setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._inner_widget = None
        self._tk_init(**kwargs)

    def set_widget(self, widget):
        self._inner_widget = widget
        self.setWidget(widget)

    def yview(self, *_args):
        if _args:
            bar = self.verticalScrollBar()
            if _args[0] == "moveto" and len(_args) > 1:
                bar.setValue(int(float(_args[1]) * bar.maximum()))
            elif _args[0] == "scroll" and len(_args) > 1:
                bar.setValue(bar.value() + int(_args[1]) * 36)
        return None

    def yview_scroll(self, number: int, _units: str):
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + number * 36)

    def configure(self, **kwargs):
        kwargs.pop("yscrollcommand", None)
        kwargs.pop("scrollregion", None)
        super().configure(**kwargs)


class Scale(TkWidgetMixin, QSlider):
    def __init__(self, parent=None, from_=0, to=100, orient=HORIZONTAL, variable: Variable | None = None,
                 command: Callable[[Any], Any] | None = None, **kwargs):
        super().__init__(Qt.Horizontal if orient == HORIZONTAL else Qt.Vertical, _parent_widget(parent))
        self._var = variable
        self.command = command
        self.setRange(int(from_), int(to))
        if self._var:
            self._var._bind_widget(self)
            self.setValue(int(self._var.get()))
        self.valueChanged.connect(self._on_value)
        self._tk_init(**kwargs)

    def _on_value(self, value: int):
        if self._var and self._var.get() != value:
            self._var.set(value)
        if self.command:
            self.command(value)

    def _sync_from_variable(self):
        if self._var:
            self.setValue(int(self._var.get()))


class Scrollbar(TkWidgetMixin, QScrollBar):
    def __init__(self, parent=None, orient=VERTICAL, command=None, **kwargs):
        super().__init__(Qt.Vertical if orient == VERTICAL else Qt.Horizontal, _parent_widget(parent))
        self.command = command
        if command is not None:
            self.valueChanged.connect(self._on_value_changed)
        self._tk_init(**kwargs)

    def set(self, *_args):
        return None

    def _on_value_changed(self, value: int):
        if self.command is None:
            return
        maximum = max(1, self.maximum())
        self.command("moveto", value / maximum)


class Notebook(TkWidgetMixin, QTabWidget):
    def __init__(self, parent=None, **kwargs):
        super().__init__(_parent_widget(parent))
        self._tk_init(**kwargs)

    def add(self, child, text: str = "", **_kwargs):
        self.addTab(child, text)


class PanedWindow(TkWidgetMixin, QSplitter):
    def __init__(self, parent=None, orient=HORIZONTAL, **kwargs):
        super().__init__(Qt.Horizontal if orient == HORIZONTAL else Qt.Vertical, _parent_widget(parent))
        self._pane_weights: list[int] = []
        self._tk_init(**kwargs)

    def add(self, child, weight: int = 1):
        self.addWidget(child)
        self._pane_weights.append(max(1, int(weight)))
        self.setStretchFactor(self.count() - 1, weight)
        QTimer.singleShot(0, self._normalize_sizes)

    def sash_place(self, *_args):
        return None

    def pack(self, side: str | None = None, fill: str | None = None, expand: bool = False,
             padx: Any = 0, pady: Any = 0, anchor: str | None = None, **kwargs):
        super().pack(side=side, fill=fill, expand=expand, padx=padx, pady=pady, anchor=anchor, **kwargs)
        self._normalize_sizes()

    def _normalize_sizes(self):
        count = self.count()
        if count <= 1:
            return
        weights = (self._pane_weights + [1] * count)[:count]
        total_weight = sum(weights)
        span = self.width() if self.orientation() == Qt.Horizontal else self.height()
        if span <= 0:
            span = 1000
        self.setSizes([max(80, int(span * weight / total_weight)) for weight in weights])


class Combobox(TkWidgetMixin, QComboBox):
    def __init__(self, parent=None, textvariable: Variable | None = None, values=(), state: str = "", **kwargs):
        super().__init__(_parent_widget(parent))
        self._var = textvariable
        self.addItems([str(v) for v in values])
        if self._var:
            self._var._bind_widget(self)
            idx = self.findText(str(self._var.get()))
            if idx >= 0:
                self.setCurrentIndex(idx)
        self.currentTextChanged.connect(self._on_changed)
        self._tk_init(**kwargs)
        if state:
            self._apply_state(state)

    def _on_changed(self, value: str):
        if self._var and self._var.get() != value:
            self._var.set(value)
        for callback in self._bindings.get("<<ComboboxSelected>>", []):
            callback(Event())

    def _sync_from_variable(self):
        if not self._var:
            return
        idx = self.findText(str(self._var.get()))
        if idx >= 0 and self.currentIndex() != idx:
            self.setCurrentIndex(idx)

    def config(self, **kwargs):
        values = kwargs.pop("values", None)
        state = kwargs.pop("state", None)
        if values is not None:
            current = self.currentText()
            self.clear()
            self.addItems([str(v) for v in values])
            idx = self.findText(current)
            if idx >= 0:
                self.setCurrentIndex(idx)
        if state is not None:
            self._apply_state(state)
        super().config(**kwargs)

    def _apply_state(self, state: str):
        self.setEnabled(state != DISABLED)
        self.setEditable(state not in (DISABLED, "readonly"))


class Separator(TkWidgetMixin, QFrame):
    def __init__(self, parent=None, orient=HORIZONTAL, **kwargs):
        super().__init__(_parent_widget(parent))
        self.setFrameShape(QFrame.HLine if orient == HORIZONTAL else QFrame.VLine)
        self._tk_init(**kwargs)


class Style:
    def theme_use(self, *_args, **_kwargs):
        return None

    def configure(self, *_args, **_kwargs):
        return None

    def map(self, *_args, **_kwargs):
        return None


class _TtkNamespace:
    Scrollbar = Scrollbar
    Notebook = Notebook
    PanedWindow = PanedWindow
    Combobox = Combobox
    Separator = Separator
    Style = Style


ttk = _TtkNamespace()


class _Messagebox:
    @staticmethod
    def showinfo(title: str, message: str, parent=None):
        _run_message_dialog(title, message, buttons=(("确定", True),), parent=parent)

    @staticmethod
    def askyesno(title: str, message: str, parent=None):
        return bool(_run_message_dialog(
            title,
            message,
            buttons=(("删除", True), ("取消", False)),
            parent=parent,
            danger=True,
        ))


messagebox = _Messagebox()


def _run_message_dialog(title: str, message: str, buttons: tuple[tuple[str, bool], ...],
                        parent=None, danger: bool = False) -> bool | None:
    """Small themed replacement for native QMessageBox to avoid blank white popups."""
    owner = _parent_widget(parent) or QApplication.activeWindow()
    dialog = QDialog(owner)
    dialog.setWindowTitle(str(title))
    dialog.setModal(True)
    dialog.setMinimumSize(420, 160)
    dialog.setStyleSheet(
        """
        QDialog { background: #1f1f1f; color: #e6e6e6; }
        QLabel { background: transparent; color: #e6e6e6; font-size: 10pt; }
        QPushButton {
            background: #2d2d2d; color: #e6e6e6; border: 1px solid #4a4a4a;
            border-radius: 8px; min-width: 86px; min-height: 32px; padding: 4px 12px;
            font-weight: 700;
        }
        QPushButton:hover { background: #333333; border-color: #6a6a6a; }
        QPushButton#dangerButton { border-color: #3794ff; color: #ffffff; }
        """
    )

    result = {"value": None}
    outer = QVBoxLayout(dialog)
    outer.setContentsMargins(18, 16, 18, 14)
    outer.setSpacing(14)

    label = QLabel(str(message), dialog)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    outer.addWidget(label, 1)

    row = QHBoxLayout()
    row.addStretch(1)
    for index, (text, value) in enumerate(buttons):
        button = QPushButton(text, dialog)
        if danger and index == 0:
            button.setObjectName("dangerButton")

        def _finish(_checked=False, selected=value):
            result["value"] = selected
            dialog.accept()

        button.clicked.connect(_finish)
        row.addWidget(button)
    outer.addLayout(row)

    dialog.exec()
    return result["value"]


class _SimpleDialog:
    @staticmethod
    def askstring(title: str, prompt: str, parent=None, initialvalue: str = ""):
        from PySide6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(_parent_widget(parent), title, prompt, text=initialvalue)
        return text if ok else None


simpledialog = _SimpleDialog()


class _ColorChooser:
    @staticmethod
    def askcolor(color: str = "#ffffff", parent=None, title: str = "选择颜色"):
        selected = QColorDialog.getColor(QColor(color), _parent_widget(parent), title)
        if not selected.isValid():
            return None
        return ((selected.red(), selected.green(), selected.blue()), selected.name())


colorchooser = _ColorChooser()
askcolor = colorchooser.askcolor
Widget = QWidget


def _margins(padx: Any, pady: Any) -> tuple[int, int, int, int]:
    left = right = _pad_value(padx)
    top = bottom = _pad_value(pady)
    if isinstance(padx, tuple):
        left, right = int(padx[0]), int(padx[1])
    if isinstance(pady, tuple):
        top, bottom = int(pady[0]), int(pady[1])
    return left, top, right, bottom


def _pad_value(value: Any) -> int:
    if isinstance(value, tuple):
        return int(value[0])
    try:
        return int(value)
    except Exception:
        return 0


def _apply_size_policy(widget: QWidget, fill: str | None, expand: bool):
    h = QSizePolicy.Expanding if fill in (X, BOTH) or expand else QSizePolicy.Preferred
    v = QSizePolicy.Expanding if fill in (Y, BOTH) or expand else QSizePolicy.Preferred
    widget.setSizePolicy(h, v)


def _alignment(anchor: str | None):
    if anchor == "w":
        return Qt.AlignLeft
    if anchor == "e":
        return Qt.AlignRight
    if anchor == "n":
        return Qt.AlignTop
    if anchor == "center":
        return Qt.AlignCenter
    return Qt.Alignment()


def _sticky_alignment(sticky: str):
    if not sticky or sticky == "nsew":
        return Qt.Alignment()
    align = Qt.Alignment()
    if "w" in sticky and "e" not in sticky:
        align |= Qt.AlignLeft
    if "e" in sticky and "w" not in sticky:
        align |= Qt.AlignRight
    if "n" in sticky and "s" not in sticky:
        align |= Qt.AlignTop
    if "s" in sticky and "n" not in sticky:
        align |= Qt.AlignBottom
    return align
