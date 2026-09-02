"""
AI 设置弹出窗口（服务商 + API Key + 模型选择）
"""
from shared import qt_compat as tk
from shared.qt_compat import ttk, messagebox

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

    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("AI 设置")
        self.geometry("760x560")
        self.configure(bg=BG_BASE)
        self.grab_set()
        self.resizable(False, False)
        self._on_save = on_save
        self._vision_label_to_key = {
            cfg.AI_PROVIDERS[key].label: key
            for key in cfg.get_vision_provider_keys()
        }
        self._vision_key_to_label = {key: label for label, key in self._vision_label_to_key.items()}
        self._build_ui()

    def _build_ui(self):
        provider_box = tk.Frame(self, bg=BG_ELEVATED, padx=12, pady=10,
                                highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        provider_box.pack(fill=tk.X, padx=20, pady=(14, 8))
        tk.Label(provider_box, text="AI Provider Matrix", bg=BG_ELEVATED, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 10, "bold")).pack(anchor="w")
        tk.Label(provider_box, text="文字功能和截图分析可使用不同模型", bg=BG_ELEVATED, fg=FG_DIM,
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

        tk.Label(form, text="文字模型:", bg=BG_BASE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9), width=9, anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        self._model_var = tk.StringVar()
        self._model_cb = ttk.Combobox(form, textvariable=self._model_var,
                                      width=50, font=(FONT_FAMILY, 9))
        self._model_cb.grid(row=1, column=1, sticky="ew", padx=(8, 0), ipady=4)

        tk.Label(form, text="截图服务:", bg=BG_BASE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9), width=9, anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        self._shot_provider_var = tk.StringVar(
            value=self._vision_key_to_label.get(cfg.SCREENSHOT_PROVIDER, "")
        )
        self._shot_provider_cb = ttk.Combobox(
            form,
            textvariable=self._shot_provider_var,
            values=tuple(self._vision_label_to_key),
            state="readonly",
            width=50,
            font=(FONT_FAMILY, 9),
        )
        self._shot_provider_cb.grid(row=2, column=1, sticky="ew", padx=(8, 0), ipady=4)
        self._shot_provider_cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_screenshot_form())

        tk.Label(form, text="截图 Key:", bg=BG_BASE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9), width=9, anchor="w").grid(row=3, column=0, sticky="w", pady=5)
        self._shot_key_var = tk.StringVar()
        tk.Entry(form, textvariable=self._shot_key_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief=tk.FLAT, font=(FONT_FAMILY, 9),
                 show="*", width=52, highlightbackground=BORDER_SUBTLE, highlightthickness=1
                 ).grid(row=3, column=1, sticky="ew", padx=(8, 0), ipady=4)

        tk.Label(form, text="截图模型:", bg=BG_BASE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9), width=9, anchor="w").grid(row=4, column=0, sticky="w", pady=5)
        self._shot_model_var = tk.StringVar(value=cfg.SCREENSHOT_MODEL)
        self._shot_model_cb = ttk.Combobox(form, textvariable=self._shot_model_var,
                                           width=50, font=(FONT_FAMILY, 9))
        self._shot_model_cb.grid(row=4, column=1, sticky="ew", padx=(8, 0), ipady=4)

        tk.Label(form, text="截图快捷键:", bg=BG_BASE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9), width=9, anchor="w").grid(row=5, column=0, sticky="w", pady=5)
        self._shortcut_var = tk.StringVar(value=cfg.SCREENSHOT_SHORTCUT)
        shortcut_row = tk.Frame(form, bg=BG_BASE)
        shortcut_row.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=5)
        shortcut_row.grid_columnconfigure(0, weight=1)
        tk.Entry(shortcut_row, textvariable=self._shortcut_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief=tk.FLAT, font=(FONT_FAMILY, 9),
                 highlightbackground=BORDER_SUBTLE, highlightthickness=1
                 ).grid(row=0, column=0, sticky="ew", ipady=4)
        ttk.Combobox(
            shortcut_row,
            textvariable=self._shortcut_var,
            values=("Ctrl+Shift+S", "Ctrl+Alt+S", "Ctrl+Shift+P", "Alt+S", "F8", "F9"),
            state="readonly",
            width=14,
            font=(FONT_FAMILY, 9),
        ).grid(row=0, column=1, sticky="e", padx=(8, 0), ipady=4)

        self._note_lbl = tk.Label(self, text="", bg=BG_BASE, fg=FG_DIM,
                                  font=(FONT_FAMILY, 8), wraplength=690, justify=tk.LEFT)
        self._note_lbl.pack(anchor="w", padx=20, pady=(2, 0))

        self._refresh_form()
        self._refresh_screenshot_form()

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
        self._note_lbl.config(text=f"{provider.note}  ·  截图分析使用下方独立的视觉模型，不跟随文字模型。")

    def _refresh_screenshot_form(self):
        label = self._shot_provider_var.get()
        provider_key = self._vision_label_to_key.get(label, cfg.SCREENSHOT_PROVIDER)
        provider = cfg.AI_PROVIDERS.get(provider_key, cfg.AI_PROVIDERS["bailian"])
        models = cfg.get_vision_models(provider.key)
        selected = cfg.SCREENSHOT_MODEL if cfg.SCREENSHOT_MODEL in models else (
            cfg.DEFAULT_SCREENSHOT_MODELS.get(provider.key) or (models[0] if models else "")
        )
        self._shot_key_var.set(getattr(cfg, provider.api_key_attr))
        self._shot_model_var.set(selected)
        self._shot_model_cb.config(values=models, state="readonly")

    def _save(self):
        from features.screenshot_prompt.widget import normalize_shortcut

        provider = cfg.AI_PROVIDERS[self._provider_var.get()]
        cfg.AI_PROVIDER = provider.key
        setattr(cfg, provider.api_key_attr, self._key_var.get().strip())
        setattr(cfg, provider.model_attr, self._model_var.get().strip())
        shot_provider_key = self._vision_label_to_key.get(self._shot_provider_var.get(), cfg.SCREENSHOT_PROVIDER)
        shot_provider = cfg.AI_PROVIDERS.get(shot_provider_key, cfg.AI_PROVIDERS["bailian"])
        cfg.SCREENSHOT_PROVIDER = shot_provider.key
        shot_key = self._shot_key_var.get().strip()
        if shot_provider.key == provider.key:
            shot_key = self._key_var.get().strip() or shot_key
        setattr(cfg, shot_provider.api_key_attr, shot_key)
        cfg.SCREENSHOT_MODEL = self._shot_model_var.get().strip()
        if not cfg.is_screenshot_model_name(shot_provider.key, cfg.SCREENSHOT_MODEL):
            messagebox.showinfo("提示", "截图模型需要从截图模型列表中选择。", parent=self)
            return
        shortcut = normalize_shortcut(self._shortcut_var.get())
        if not shortcut:
            messagebox.showinfo("提示", "截图快捷键无效，请输入例如 Ctrl+Shift+S 的格式。", parent=self)
            return
        cfg.SCREENSHOT_SHORTCUT = shortcut
        cfg.save_ai_config()
        if self._on_save:
            self._on_save()
        self.destroy()
