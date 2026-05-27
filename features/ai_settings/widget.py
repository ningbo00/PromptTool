"""
AI 设置弹出窗口（服务商 + API Key + 模型选择）
"""
import tkinter as tk
from tkinter import ttk

import shared.config as cfg
from shared.ui_kit import (
    BG_BASE, BG_ELEVATED, BG_CARD, BG_HOVER, BORDER_SUBTLE,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_PURPLE,
    ACCENT_CYAN, FONT_FAMILY,
)


PROVIDER_COLORS = {
    "kimi": ACCENT_BLUE,
    "bailian": ACCENT_YELLOW,
    "doubao": ACCENT_CYAN,
    "deepseek": ACCENT_GREEN,
    "openai": ACCENT_PURPLE,
}


class AISettingsDialog(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("AI 设置")
        self.geometry("640x340")
        self.configure(bg=BG_BASE)
        self.grab_set()
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        provider_box = tk.Frame(self, bg=BG_ELEVATED, padx=12, pady=10,
                                highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        provider_box.pack(fill=tk.X, padx=20, pady=(14, 8))
        tk.Label(provider_box, text="AI Provider Matrix", bg=BG_ELEVATED, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 10, "bold")).pack(anchor="w")
        tk.Label(provider_box, text="选择平台后填写对应 Key 和模型", bg=BG_ELEVATED, fg=FG_DIM,
                 font=(FONT_FAMILY, 8)).pack(anchor="w", pady=(1, 0))

        provider_grid = tk.Frame(provider_box, bg=BG_ELEVATED)
        provider_grid.pack(fill=tk.X, pady=(6, 0))
        self._provider_var = tk.StringVar(value=cfg.AI_PROVIDER)
        for idx, provider in enumerate(cfg.AI_PROVIDERS.values()):
            tk.Radiobutton(
                provider_grid,
                text=provider.label,
                variable=self._provider_var,
                value=provider.key,
                bg=BG_ELEVATED,
                fg=PROVIDER_COLORS.get(provider.key, FG_PRIMARY),
                activebackground=BG_ELEVATED,
                selectcolor=BG_CARD,
                font=(FONT_FAMILY, 9),
                command=self._refresh_form,
            ).grid(row=idx // 3, column=idx % 3, sticky="w", padx=(0, 18), pady=2)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=20, pady=(0, 8))

        form = tk.Frame(self, bg=BG_BASE)
        form.pack(fill=tk.X, padx=20)
        form.grid_columnconfigure(1, weight=1)

        tk.Label(form, text="API Key:", bg=BG_BASE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9), width=9, anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        self._key_var = tk.StringVar()
        tk.Entry(form, textvariable=self._key_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief=tk.FLAT, font=(FONT_FAMILY, 9),
                 show="*", width=52, highlightbackground=BORDER_SUBTLE, highlightthickness=1
                 ).grid(row=0, column=1, sticky="ew", padx=(8, 0), ipady=4)

        tk.Label(form, text="模型:", bg=BG_BASE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9), width=9, anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        self._model_var = tk.StringVar()
        self._model_cb = ttk.Combobox(form, textvariable=self._model_var,
                                      width=50, font=(FONT_FAMILY, 9))
        self._model_cb.grid(row=1, column=1, sticky="ew", padx=(8, 0), ipady=4)

        self._note_lbl = tk.Label(self, text="", bg=BG_BASE, fg=FG_DIM,
                                  font=(FONT_FAMILY, 8), wraplength=590, justify=tk.LEFT)
        self._note_lbl.pack(anchor="w", padx=20, pady=(2, 0))

        self._refresh_form()

        btn_row = tk.Frame(self, bg=BG_BASE)
        btn_row.pack(pady=(14, 14))
        tk.Button(btn_row, text="保存", command=self._save,
                  bg=BG_CARD, fg=ACCENT_GREEN, relief=tk.FLAT,
                  font=(FONT_FAMILY, 9, "bold"), padx=20, pady=4,
                  cursor="hand2", activebackground=BG_HOVER,
                  highlightbackground=ACCENT_GREEN, highlightthickness=1).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_row, text="取消", command=self.destroy,
                  bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
                  font=(FONT_FAMILY, 9, "bold"), padx=20, pady=4,
                  cursor="hand2", activebackground=BG_HOVER).pack(side=tk.LEFT)

    def _refresh_form(self):
        provider = cfg.AI_PROVIDERS[self._provider_var.get()]
        self._key_var.set(getattr(cfg, provider.api_key_attr))
        self._model_var.set(getattr(cfg, provider.model_attr))
        self._model_cb.config(values=provider.models, state="readonly")
        self._note_lbl.config(text=provider.note)

    def _save(self):
        provider = cfg.AI_PROVIDERS[self._provider_var.get()]
        cfg.AI_PROVIDER = provider.key
        setattr(cfg, provider.api_key_attr, self._key_var.get().strip())
        setattr(cfg, provider.model_attr, self._model_var.get().strip())
        cfg.save_ai_config()
        self.destroy()
