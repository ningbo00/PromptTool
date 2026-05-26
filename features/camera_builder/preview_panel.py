import tkinter as tk


class PreviewPanel:
    @staticmethod
    def write_text(widget, text: str) -> None:
        if widget is None:
            return
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        if text:
            widget.insert("1.0", text)
        widget.config(state=tk.DISABLED)

    @classmethod
    def render(cls, *, preview_text, preview_zh_text, neg_preview_text,
               neg_zh_preview_text, prompt, prompt_zh,
               negative_text="", negative_zh="") -> None:
        cls.write_text(preview_text, prompt)
        cls.write_text(preview_zh_text, prompt_zh)
        cls.write_text(neg_preview_text, negative_text)
        cls.write_text(neg_zh_preview_text, negative_zh)
