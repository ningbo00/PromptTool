"""
AI HTTP 客户端：调用 Kimi / 阿里百炼 API 的公共函数
"""
import json
import threading
import urllib.request
import urllib.error

from PySide6.QtCore import QObject, QCoreApplication, Signal


class _CallbackDispatcher(QObject):
    delivered = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.delivered.connect(self._invoke)

    def _invoke(self, callback, args):
        callback(*args)


_dispatcher = None


def _get_dispatcher():
    global _dispatcher
    app = QCoreApplication.instance()
    if app is None:
        return None
    if _dispatcher is None:
        _dispatcher = _CallbackDispatcher()
        _dispatcher.moveToThread(app.thread())
    return _dispatcher


def _deliver(callback, *args) -> None:
    if callback is None:
        return
    dispatcher = _get_dispatcher()
    if dispatcher is None:
        callback(*args)
    else:
        dispatcher.delivered.emit(callback, args)


def call_ai(url: str, key: str, model: str, messages: list,
            temperature: float = 0.7,
            on_success=None, on_error=None, max_tokens: int | None = None,
            timeout_s: int = 60) -> None:
    """
    异步调用 AI API。
    on_success(result_text: str) / on_error(error_msg: str) 会投递回 Qt 主线程。
    若不传回调，则阻塞并返回 (result, error) 元组。
    """
    payload_data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload_data["max_tokens"] = max_tokens
    payload = json.dumps(payload_data).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    _get_dispatcher()

    def _run():
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"].get("content", "")
            if isinstance(content, list):
                result = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                ).strip()
            else:
                result = str(content).strip()
            if not result:
                raise ValueError(f"AI 返回为空：{json.dumps(body, ensure_ascii=False)[:500]}")
            _deliver(on_success, result)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            msg = f"HTTP {e.code}: {err_body[:800]}"
            _deliver(on_error, msg)
        except Exception as e:
            _deliver(on_error, str(e))

    threading.Thread(target=_run, daemon=True).start()
