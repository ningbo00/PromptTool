import tkinter as tk
from tkinter import ttk

from shared.ui_kit import (
    BG_BASE, BG_ELEVATED, BG_SURFACE, BG_CARD, BG_HOVER, BORDER_SUBTLE,
    FG_PRIMARY, FG_MUTED, ACCENT_GREEN, ACCENT_YELLOW,
    ACCENT_RED, ACCENT_ORANGE, ACCENT_CYAN, FONT_FAMILY,
)


class PreviewPanel:
    @classmethod
    def build(cls, builder, parent):
        parent.configure(bg=BG_SURFACE)

        header = tk.Frame(parent, bg=BG_SURFACE)
        header.pack(fill=tk.X, padx=10, pady=(10, 2))
        tk.Label(header, text="Output Deck", bg=BG_SURFACE, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 10, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="preview / copy / insert", bg=BG_SURFACE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 8)).pack(side=tk.RIGHT)

        extra_row = tk.Frame(parent, bg=BG_SURFACE)
        extra_row.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(extra_row, text="附加词:", bg=BG_SURFACE, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9)).pack(side=tk.LEFT)
        extra_entry = tk.Entry(extra_row, textvariable=builder.extra_var, bg=BG_CARD, fg=FG_PRIMARY,
                               insertbackground=FG_PRIMARY, relief=tk.FLAT, font=(FONT_FAMILY, 9),
                               highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        extra_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(8, 0))
        extra_entry.bind("<KeyRelease>", lambda _e: builder._generate())

        # ── 外层：左右水平分栏 ──────────────────────────────────────
        h_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        h_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 8))

        # ── 左列：垂直分栏 → 正面(英文) / 负面(英文) ─────────────────
        en_col = tk.Frame(h_paned, bg=BG_SURFACE)
        h_paned.add(en_col, weight=3)

        en_v_paned = ttk.PanedWindow(en_col, orient=tk.VERTICAL)
        en_v_paned.pack(fill=tk.BOTH, expand=True)

        # 正面英文
        en_pos_outer = tk.Frame(en_v_paned, bg=BG_SURFACE)
        en_v_paned.add(en_pos_outer, weight=3)
        en_pos_hdr = tk.Frame(en_pos_outer, bg=BG_SURFACE)
        en_pos_hdr.pack(fill=tk.X, pady=(4, 2))
        tk.Label(en_pos_hdr, text="🔤 正面提示词", bg=BG_SURFACE, fg=ACCENT_GREEN,
                 font=(FONT_FAMILY, 8, "bold")).pack(side=tk.LEFT, padx=6)
        en_pos_frame = tk.Frame(en_pos_outer, bg=BG_SURFACE)
        en_pos_frame.pack(fill=tk.BOTH, expand=True)
        builder.preview_text = tk.Text(en_pos_frame, bg=BG_SURFACE, fg=ACCENT_GREEN,
                                    relief=tk.FLAT, font=(FONT_FAMILY, 9),
                                    wrap=tk.WORD, padx=8, pady=6, state=tk.DISABLED)
        en_pos_sb = ttk.Scrollbar(en_pos_frame, orient="vertical", command=builder.preview_text.yview)
        builder.preview_text.configure(yscrollcommand=en_pos_sb.set)
        builder.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        en_pos_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # 负面英文
        en_neg_outer = tk.Frame(en_v_paned, bg=BG_SURFACE)
        en_v_paned.add(en_neg_outer, weight=2)
        en_neg_hdr = tk.Frame(en_neg_outer, bg=BG_SURFACE)
        en_neg_hdr.pack(fill=tk.X, pady=(6, 2))
        tk.Label(en_neg_hdr, text="🚫 负面提示词", bg=BG_SURFACE, fg=ACCENT_RED,
                 font=(FONT_FAMILY, 8, "bold")).pack(side=tk.LEFT, padx=6)

        def _copy_neg():
            import pyperclip
            txt = builder.neg_preview_text.get("1.0", tk.END).strip() if builder.neg_preview_text else ""
            if txt:
                pyperclip.copy(txt)
                _copy_neg_btn.config(text="✓ 已复制")
                builder.after(1500, lambda: _copy_neg_btn.config(text="📋 复制负面词"))

        def _toggle_neg_positive():
            builder.neg_to_positive_enabled.set(not builder.neg_to_positive_enabled.get())
            on = builder.neg_to_positive_enabled.get()
            builder._neg_btn_ref.config(
                text="● 已转正面排除词" if on else "○ 转为正面排除词",
                bg=BG_CARD,
                fg=ACCENT_ORANGE if on else FG_PRIMARY,
            )
            builder._generate()

        _copy_neg_btn = tk.Button(
            en_neg_hdr, text="📋 复制负面词", command=_copy_neg,
            bg=BG_CARD, fg=ACCENT_CYAN, relief=tk.FLAT,
            font=(FONT_FAMILY, 8, "bold"), padx=8, pady=1, cursor="hand2",
            activebackground=BG_HOVER,
            highlightbackground=ACCENT_CYAN, highlightthickness=1,
        )
        _copy_neg_btn.pack(side=tk.RIGHT, padx=(0, 6))

        _neg_btn = tk.Button(
            en_neg_hdr, text="○ 转为正面排除词", command=_toggle_neg_positive,
            bg=BG_CARD, fg=FG_PRIMARY, relief=tk.FLAT,
            font=(FONT_FAMILY, 8, "bold"), padx=8, pady=1, cursor="hand2",
            activebackground=BG_HOVER,
            highlightbackground=ACCENT_ORANGE, highlightthickness=1,
        )
        _neg_btn.pack(side=tk.RIGHT, padx=(0, 4))
        builder._neg_btn_ref = _neg_btn

        en_neg_frame = tk.Frame(en_neg_outer, bg=BG_SURFACE)
        en_neg_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        builder.neg_preview_text = tk.Text(
            en_neg_frame, bg=BG_SURFACE, fg=ACCENT_RED,
            relief=tk.FLAT, font=(FONT_FAMILY, 9),
            wrap=tk.WORD, padx=8, pady=4, state=tk.DISABLED,
        )
        en_neg_sb = ttk.Scrollbar(en_neg_frame, orient="vertical", command=builder.neg_preview_text.yview)
        builder.neg_preview_text.configure(yscrollcommand=en_neg_sb.set)
        builder.neg_preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        en_neg_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # ── 右列：垂直分栏 → 正面(中文) / 负面(中文) ─────────────────
        zh_col = tk.Frame(h_paned, bg=BG_BASE)
        h_paned.add(zh_col, weight=2)

        zh_v_paned = ttk.PanedWindow(zh_col, orient=tk.VERTICAL)
        zh_v_paned.pack(fill=tk.BOTH, expand=True)

        # 正面中文
        zh_pos_outer = tk.Frame(zh_v_paned, bg=BG_BASE)
        zh_v_paned.add(zh_pos_outer, weight=3)
        tk.Label(zh_pos_outer, text="🀄 正面中文对照", bg=BG_BASE, fg=ACCENT_YELLOW,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", padx=6, pady=(4, 2))
        zh_pos_frame = tk.Frame(zh_pos_outer, bg=BG_BASE)
        zh_pos_frame.pack(fill=tk.BOTH, expand=True)
        builder.preview_zh_text = tk.Text(zh_pos_frame, bg=BG_BASE, fg=ACCENT_YELLOW,
                                       relief=tk.FLAT, font=(FONT_FAMILY, 9),
                                       wrap=tk.WORD, padx=8, pady=6, state=tk.DISABLED)
        zh_pos_sb = ttk.Scrollbar(zh_pos_frame, orient="vertical", command=builder.preview_zh_text.yview)
        builder.preview_zh_text.configure(yscrollcommand=zh_pos_sb.set)
        builder.preview_zh_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        zh_pos_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # 负面中文
        zh_neg_outer = tk.Frame(zh_v_paned, bg=BG_BASE)
        zh_v_paned.add(zh_neg_outer, weight=2)
        tk.Label(zh_neg_outer, text="🀄 负面中文对照", bg=BG_BASE, fg=ACCENT_RED,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", padx=6, pady=(6, 2))
        zh_neg_frame = tk.Frame(zh_neg_outer, bg=BG_BASE)
        zh_neg_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        builder.neg_zh_preview_text = tk.Text(
            zh_neg_frame, bg=BG_BASE, fg=ACCENT_RED,
            relief=tk.FLAT, font=(FONT_FAMILY, 9),
            wrap=tk.WORD, padx=8, pady=4, state=tk.DISABLED,
        )
        zh_neg_sb = ttk.Scrollbar(zh_neg_frame, orient="vertical", command=builder.neg_zh_preview_text.yview)
        builder.neg_zh_preview_text.configure(yscrollcommand=zh_neg_sb.set)
        builder.neg_zh_preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        zh_neg_sb.pack(side=tk.RIGHT, fill=tk.Y)
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
