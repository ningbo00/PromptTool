from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


def test_screenshot_selector_cancel_is_idempotent():
    from shared.qt_compat import _app
    from features.screenshot_prompt.widget import ScreenshotSelector

    app = _app()
    calls = []
    selector = ScreenshotSelector(
        on_selected=lambda _pixmap: calls.append("selected"),
        on_cancel=lambda: calls.append("cancel"),
    )
    app.processEvents()

    selector._cancel()
    selector._cancel()
    app.processEvents()

    assert calls == ["cancel"]


def test_screenshot_selector_finish_selected_once():
    from shared.qt_compat import _app
    from features.screenshot_prompt.widget import ScreenshotSelector

    app = _app()
    calls = []
    selector = ScreenshotSelector(
        on_selected=lambda pixmap: calls.append(("selected", isinstance(pixmap, QPixmap))),
        on_cancel=lambda: calls.append(("cancel", False)),
    )
    app.processEvents()

    selector._finish(QPixmap(10, 10))
    selector._cancel()
    app.processEvents()

    assert calls == [("selected", True)]


def test_screenshot_selector_right_click_cancels():
    from shared.qt_compat import _app
    from features.screenshot_prompt.widget import ScreenshotSelector

    class Event:
        def button(self):
            return Qt.RightButton

    app = _app()
    calls = []
    selector = ScreenshotSelector(
        on_selected=lambda _pixmap: calls.append("selected"),
        on_cancel=lambda: calls.append("cancel"),
    )
    app.processEvents()

    selector.mousePressEvent(Event())
    app.processEvents()

    assert calls == ["cancel"]
