import json
import time

from PySide6.QtCore import QThread


def test_call_ai_delivers_callbacks_on_qt_main_thread(monkeypatch):
    from shared.qt_compat import _app
    from features.ai_optimize.client import call_ai

    app = _app()
    main_thread = app.thread()
    result = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "generated prompt"}}]
            }).encode("utf-8")

    def fake_urlopen(_req, timeout=0):
        assert timeout == 60
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    call_ai(
        "https://example.test/chat",
        "key",
        "model",
        [{"role": "user", "content": "hi"}],
        on_success=lambda text: result.update(text=text, thread=QThread.currentThread()),
        on_error=lambda err: result.update(error=err, thread=QThread.currentThread()),
    )

    deadline = time.time() + 2
    while "text" not in result and "error" not in result and time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)

    assert result == {"text": "generated prompt", "thread": main_thread}
