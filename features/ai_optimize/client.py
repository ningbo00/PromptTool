"""
AI HTTP 客户端：调用 Kimi / 阿里百炼 API 的公共函数
"""
import json
import threading
import urllib.request
import urllib.error


def call_ai(url: str, key: str, model: str, messages: list,
            temperature: float = 0.7,
            on_success=None, on_error=None) -> None:
    """
    异步调用 AI API。
    on_success(result_text: str) 在主线程通过 widget.after(0, ...) 回调。
    on_error(error_msg: str) 同理。
    若不传回调，则阻塞并返回 (result, error) 元组。
    """
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }

    def _run():
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            result = body["choices"][0]["message"]["content"].strip()
            if on_success:
                on_success(result)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            msg = f"HTTP {e.code}: {err_body[:200]}"
            if on_error:
                on_error(msg)
        except Exception as e:
            if on_error:
                on_error(str(e))

    threading.Thread(target=_run, daemon=True).start()
