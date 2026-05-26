"""
AI 设置弹出窗口（服务商 + API Key + 模型 选择）
"""
import tkinter as tk
from tkinter import ttk

import shared.config as cfg
from shared.ui_kit import (
    BG_BASE, BG_CARD, FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_YELLOW, BG_HOVER, DARK_TEXT,
)


KIMI_MODELS = [
    "kimi-k2.5", "kimi-k2-0905-preview", "kimi-k2-thinking",
    "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k",
]
BAILIAN_MODELS = [
    "qwen-max", "qwen-max-latest", "qwen-plus", "qwen-turbo",
    "qwen-long", "qwen2.5-72b-instruct", "qwen2.5-14b-instruct",
    "qwen2.5-7b-instruct",
]


class AISettingsDialog(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("AI 设置")
        self.geometry("520x280")
        self.configure(bg=BG_BASE)
        self.grab_set()
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        # 服务商选择
        provider_row = tk.Frame(self, bg=BG_BASE)
        provider_row.pack(fill=tk.X, padx=20, pady=(14, 8))
        tk.Label(provider_row, text="当前服务商:", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)

        self._provider_var = tk.StringVar(value=cfg.AI_PROVIDER)
        for val, txt, col in [("kimi", "Kimi (Moonshot)", ACCENT_BLUE),
                               ("bailian", "阿里百炼 (Qwen)", ACCENT_YELLOW)]:
            tk.Radiobutton(provider_row, text=txt, variable=self._provider_var, value=val,
                           bg=BG_BASE, fg=col, activebackground=BG_BASE,
                           selectcolor=BG_CARD, font=("微软雅黑", 9),
                           command=self._refresh_form).pack(side=tk.LEFT, padx=(12, 0))

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=20, pady=(0, 8))

        form = tk.Frame(self, bg=BG_BASE)
        form.pack(fill=tk.X, padx=20)
        form.grid_columnconfigure(1, weight=1)

        tk.Label(form, text="API Key:", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9), width=9, anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        self._key_var = tk.StringVar()
        tk.Entry(form, textvariable=self._key_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief=tk.FLAT, font=("微软雅黑", 9),
                 show="*", width=42).grid(row=0, column=1, sticky="ew", padx=(8, 0), ipady=4)

        tk.Label(form, text="模型:", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9), width=9, anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        self._model_var = tk.StringVar()
        self._model_cb = ttk.Combobox(form, textvariable=self._model_var,
                                       width=40, font=("微软雅黑", 9))
        self._model_cb.grid(row=1, column=1, sticky="ew", padx=(8, 0), ipady=4)

        self._note_lbl = tk.Label(self, text="", bg=BG_BASE, fg=FG_DIM,
                                   font=("微软雅黑", 8))
        self._note_lbl.pack(anchor="w", padx=20, pady=(2, 0))

        self._refresh_form()

        btn_row = tk.Frame(self, bg=BG_BASE)
        btn_row.pack(pady=(12, 14))
        tk.Button(btn_row, text="保存", command=self._save,
                  bg=ACCENT_GREEN, fg=DARK_TEXT, relief=tk.FLAT,
                  font=("微软雅黑", 9, "bold"), padx=20, pady=4,
                  cursor="hand2", activebackground=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_row, text="取消", command=self.destroy,
                  bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
                  font=("微软雅黑", 9, "bold"), padx=20, pady=4,
                  cursor="hand2", activebackground=BG_HOVER).pack(side=tk.LEFT)

    def _refresh_form(self):
        p = self._provider_var.get()
        if p == "kimi":
            self._key_var.set(cfg.KIMI_API_KEY)
            self._model_var.set(cfg.KIMI_MODEL)
            self._model_cb.config(values=KIMI_MODELS, state="readonly")
            self._note_lbl.config(text="API 文档: platform.moonshot.cn  ·  端点: api.moonshot.cn")
        else:
            self._key_var.set(cfg.BAILIAN_API_KEY)
            self._model_var.set(cfg.BAILIAN_MODEL)
            self._model_cb.config(values=BAILIAN_MODELS, state="readonly")
            self._note_lbl.config(
                text="API 文档: bailian.console.aliyun.com  ·  端点: dashscope.aliyuncs.com")

    def _save(self):
        cfg.AI_PROVIDER = self._provider_var.get()
        if cfg.AI_PROVIDER == "kimi":
            cfg.KIMI_API_KEY = self._key_var.get().strip()
            cfg.KIMI_MODEL   = self._model_var.get().strip()
        else:
            cfg.BAILIAN_API_KEY = self._key_var.get().strip()
            cfg.BAILIAN_MODEL   = self._model_var.get().strip()
        cfg.save_ai_config()
        self.destroy()
