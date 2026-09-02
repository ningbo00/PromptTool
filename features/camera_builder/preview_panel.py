from shared import qt_compat as tk
from shared.qt_compat import ttk

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

        deck = tk.Frame(parent, bg=BG_SURFACE)
        deck.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 8))
        deck.grid_columnconfigure(0, weight=3, minsize=300)
        deck.grid_columnconfigure(1, weight=2, minsize=260)
        deck.grid_rowconfigure(0, weight=3)
        deck.grid_rowconfigure(2, weight=2)

        en_pos_outer = tk.Frame(deck, bg=BG_SURFACE)
        en_pos_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 6))
        en_pos_hdr = tk.Frame(en_pos_outer, bg=BG_SURFACE)
        en_pos_hdr.pack(fill=tk.X, pady=(0, 2))
        tk.Label(en_pos_hdr, text="🔤 正面提示词", bg=BG_SURFACE, fg=ACCENT_GREEN,
                 font=(FONT_FAMILY, 8, "bold")).pack(side=tk.LEFT, padx=6)
        builder.preview_text = tk.Text(en_pos_outer, bg=BG_SURFACE, fg=ACCENT_GREEN,
                                    relief=tk.FLAT, font=(FONT_FAMILY, 9),
                                    wrap=tk.WORD, padx=8, pady=6, state=tk.DISABLED)

        cls._pack_text_area(en_pos_outer, builder.preview_text)

        divider = tk.Frame(deck, bg=BORDER_SUBTLE)
        divider.setMaximumHeight(1)
        divider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        en_neg_outer = tk.Frame(deck, bg=BG_SURFACE)
        en_neg_outer.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        en_neg_hdr = tk.Frame(en_neg_outer, bg=BG_SURFACE)
        en_neg_hdr.pack(fill=tk.X, pady=(0, 2))
        tk.Label(en_neg_hdr, text="🚫 负面提示词", bg=BG_SURFACE, fg=ACCENT_RED,
                 font=(FONT_FAMILY, 8, "bold")).pack(side=tk.LEFT, padx=6)

        def _copy_neg(_checked=False):
            import pyperclip
            txt = builder.neg_preview_text.get("1.0", tk.END).strip() if builder.neg_preview_text else ""
            if txt:
                pyperclip.copy(txt)
                _copy_neg_btn.config(text="✓ 已复制")
                builder.after(1500, lambda: _copy_neg_btn.config(text="📋 复制负面词"))

        def _toggle_neg_positive(_checked=False):
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

        builder.neg_preview_text = tk.Text(
            en_neg_outer, bg=BG_SURFACE, fg=ACCENT_RED,
            relief=tk.FLAT, font=(FONT_FAMILY, 9),
            wrap=tk.WORD, padx=8, pady=4, state=tk.DISABLED,
        )
        cls._pack_text_area(en_neg_outer, builder.neg_preview_text)

        zh_pos_outer = tk.Frame(deck, bg=BG_BASE)
        zh_pos_outer.grid(row=0, column=1, sticky="nsew", pady=(0, 6))
        tk.Label(zh_pos_outer, text="🀄 正面中文对照", bg=BG_BASE, fg=ACCENT_YELLOW,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", padx=6, pady=(0, 2))
        builder.preview_zh_text = tk.Text(zh_pos_outer, bg=BG_BASE, fg=ACCENT_YELLOW,
                                       relief=tk.FLAT, font=(FONT_FAMILY, 9),
                                       wrap=tk.WORD, padx=8, pady=6, state=tk.DISABLED)
        cls._pack_text_area(zh_pos_outer, builder.preview_zh_text)

        zh_neg_outer = tk.Frame(deck, bg=BG_BASE)
        zh_neg_outer.grid(row=2, column=1, sticky="nsew")
        tk.Label(zh_neg_outer, text="🀄 负面中文对照", bg=BG_BASE, fg=ACCENT_RED,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", padx=6, pady=(0, 2))
        builder.neg_zh_preview_text = tk.Text(
            zh_neg_outer, bg=BG_BASE, fg=ACCENT_RED,
            relief=tk.FLAT, font=(FONT_FAMILY, 9),
            wrap=tk.WORD, padx=8, pady=4, state=tk.DISABLED,
        )
        cls._pack_text_area(zh_neg_outer, builder.neg_zh_preview_text)

    @staticmethod
    def _pack_text_area(parent, text_widget):
        text_widget.setLineWrapColumnOrWidth(0)
        text_widget.setMinimumWidth(0)
        text_widget.setMaximumWidth(16777215)
        sb = ttk.Scrollbar(parent, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=sb.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

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
