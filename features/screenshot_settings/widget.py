"""Screenshot reverse-prompt planning settings."""
from __future__ import annotations

from shared import qt_compat as tk
from shared.qt_compat import ttk

import shared.config as cfg
from features.screenshot_prompt.widget import SCREENSHOT_ANALYSIS_MODES
from shared.ui_kit import (
    BG_BASE, BG_ELEVATED, BG_CARD, BG_HOVER, BORDER_SUBTLE,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, FONT_FAMILY,
)


DETAIL_LABEL_TO_KEY = {
    "完整提示词": "full",
    "精简提示词": "concise",
}
DETAIL_KEY_TO_LABEL = {value: key for key, value in DETAIL_LABEL_TO_KEY.items()}


class ScreenshotSettingsDialog(tk.Toplevel):
    """Choose how the next screenshot reverse prompt should be analyzed."""

    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("截图分析设置")
        self.geometry("640x520")
        self.minsize(600, 480)
        self.configure(bg=BG_BASE)
        self.grab_set()
        self.resizable(True, True)
        self._on_save = on_save
        self._label_to_key = {
            spec.label: key
            for key, spec in SCREENSHOT_ANALYSIS_MODES.items()
        }
        self._key_to_label = {key: label for label, key in self._label_to_key.items()}
        self._mode_var = tk.StringVar(
            value=self._key_to_label.get(cfg.SCREENSHOT_ANALYSIS_MODE, "完整反推")
        )
        self._detail_var = tk.StringVar(
            value=DETAIL_KEY_TO_LABEL.get(cfg.SCREENSHOT_PROMPT_DETAIL, "完整提示词")
        )
        self._build_ui()

    def _build_ui(self):
        shell = tk.Frame(self, bg=BG_BASE)
        shell.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)

        header = tk.Frame(
            shell, bg=BG_ELEVATED, padx=14, pady=12,
            highlightbackground=BORDER_SUBTLE, highlightthickness=1,
        )
        header.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            header, text="Screenshot Plan", bg=BG_ELEVATED, fg=FG_PRIMARY,
            font=(FONT_FAMILY, 11, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="先在这里选择反推用途；之后点击截图或按全局快捷键，就会按这个计划分析。",
            bg=BG_ELEVATED, fg=FG_DIM, font=(FONT_FAMILY, 8), wraplength=560,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(2, 0))

        form = tk.Frame(shell, bg=BG_BASE)
        form.pack(fill=tk.X, pady=(0, 10))
        form.grid_columnconfigure(1, weight=1)
        tk.Label(
            form, text="反推用途", bg=BG_BASE, fg=FG_MUTED,
            font=(FONT_FAMILY, 9, "bold"), width=9, anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=4)
        self._mode_cb = ttk.Combobox(
            form,
            textvariable=self._mode_var,
            values=tuple(self._label_to_key),
            state="readonly",
            width=34,
            font=(FONT_FAMILY, 9),
        )
        self._mode_cb.grid(row=0, column=1, sticky="ew", padx=(8, 0), ipady=4)
        self._mode_cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_description())

        tk.Label(
            form, text="生成长度", bg=BG_BASE, fg=FG_MUTED,
            font=(FONT_FAMILY, 9, "bold"), width=9, anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=4)
        self._detail_cb = ttk.Combobox(
            form,
            textvariable=self._detail_var,
            values=tuple(DETAIL_LABEL_TO_KEY),
            state="readonly",
            width=34,
            font=(FONT_FAMILY, 9),
        )
        self._detail_cb.grid(row=1, column=1, sticky="ew", padx=(8, 0), ipady=4)
        self._detail_cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_description())

        self._desc_label = tk.Label(
            shell, text="", bg=BG_ELEVATED, fg=FG_MUTED,
            font=(FONT_FAMILY, 9), wraplength=570, justify=tk.LEFT,
            padx=12, pady=10, highlightbackground=BORDER_SUBTLE,
            highlightthickness=1,
        )
        self._desc_label.pack(fill=tk.X, pady=(0, 10))

        custom_box = tk.Frame(
            shell, bg=BG_ELEVATED, padx=12, pady=10,
            highlightbackground=BORDER_SUBTLE, highlightthickness=1,
        )
        custom_box.pack(fill=tk.BOTH, expand=True)
        tk.Label(
            custom_box, text="自定义要求", bg=BG_ELEVATED, fg=FG_PRIMARY,
            font=(FONT_FAMILY, 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            custom_box,
            text="选择“自定义”时会直接使用这里的要求；其他模式下也会保存，方便下次切回。",
            bg=BG_ELEVATED, fg=FG_DIM, font=(FONT_FAMILY, 8), wraplength=540,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(1, 8))
        self._custom_text = tk.Text(
            custom_box, bg=BG_CARD, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief=tk.FLAT, font=(FONT_FAMILY, 9), wrap=tk.WORD,
            padx=10, pady=8, highlightbackground=BORDER_SUBTLE,
            highlightthickness=1,
        )
        self._custom_text.pack(fill=tk.BOTH, expand=True)
        self._custom_text.setPlaceholderText(
            "例如：只分析角色的盔甲材质和轮廓语言，输出英文关键词，不写背景。"
        )
        if cfg.SCREENSHOT_ANALYSIS_CUSTOM:
            self._custom_text.insert("1.0", cfg.SCREENSHOT_ANALYSIS_CUSTOM)

        btn_row = tk.Frame(shell, bg=BG_BASE)
        btn_row.pack(fill=tk.X, pady=(12, 0))
        tk.Button(
            btn_row, text="保存计划", command=self._save,
            bg=BG_CARD, fg=ACCENT_GREEN, relief=tk.FLAT,
            font=(FONT_FAMILY, 9, "bold"), padx=20, pady=5,
            cursor="hand2", activebackground=BG_HOVER,
            highlightbackground=ACCENT_GREEN, highlightthickness=1,
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            btn_row, text="取消", command=self.destroy,
            bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
            font=(FONT_FAMILY, 9, "bold"), padx=18, pady=5,
            cursor="hand2", activebackground=BG_HOVER,
        ).pack(side=tk.LEFT)
        tk.Label(
            btn_row, text="模式会写入本地 ai_config.json", bg=BG_BASE,
            fg=ACCENT_BLUE, font=(FONT_FAMILY, 8),
        ).pack(side=tk.RIGHT)

        self._refresh_description()

    def _selected_key(self) -> str:
        return self._label_to_key.get(self._mode_var.get(), "full_reverse")

    def _selected_detail(self) -> str:
        return DETAIL_LABEL_TO_KEY.get(self._detail_var.get(), "full")

    def _refresh_description(self):
        spec = SCREENSHOT_ANALYSIS_MODES[self._selected_key()]
        detail = "适合直接生图，短关键词为主。" if self._selected_detail() == "concise" else "信息更完整，适合保存、二次编辑和视频生成。"
        self._desc_label.config(text=f"{spec.label}：{spec.description}\n长度：{detail}\n重点：{spec.focus}")

    def _save(self):
        cfg.SCREENSHOT_ANALYSIS_MODE = self._selected_key()
        cfg.SCREENSHOT_ANALYSIS_CUSTOM = self._custom_text.get("1.0", tk.END).strip()
        cfg.SCREENSHOT_PROMPT_DETAIL = self._selected_detail()
        cfg.save_ai_config()
        if self._on_save:
            self._on_save()
        self.destroy()
