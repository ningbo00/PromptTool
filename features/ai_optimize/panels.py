import tkinter as tk
from tkinter import ttk

from shared.ui_kit import (
    BG_BASE, BG_SURFACE, BG_CARD, BG_HOVER,
    FG_PRIMARY, FG_MUTED,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_RED, ACCENT_ORANGE,
    DARK_TEXT, Tooltip,
)


class InstructionPanel:
    def __init__(self, parent, presets, length_var):
        self.frame = tk.Frame(parent, bg=BG_SURFACE, padx=10, pady=8)
        self.frame.pack(fill=tk.X, padx=12, pady=(10, 6))
        self.preset_var = tk.StringVar(value=presets[0])
        self.custom_var = tk.StringVar()

        tk.Label(self.frame, text="指令", bg=BG_SURFACE, fg=FG_PRIMARY,
                 font=("微软雅黑", 10, "bold")).pack(anchor="w", pady=(0, 6))
        self._build_options(presets, length_var)
        self._build_custom_input()

    def _build_options(self, presets, length_var):
        row = tk.Frame(self.frame, bg=BG_SURFACE)
        row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(row, text="优化方向:", bg=BG_SURFACE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=self.preset_var, values=presets,
                     state="readonly", width=30, font=("微软雅黑", 9)
                     ).pack(side=tk.LEFT, padx=(6, 12))

        tk.Label(row, text="输出长度:", bg=BG_SURFACE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        for label in ("简短", "中等", "详细"):
            tk.Radiobutton(row, text=label, variable=length_var, value=label,
                           bg=BG_SURFACE, fg=FG_PRIMARY, activebackground=BG_SURFACE,
                           selectcolor=BG_CARD, font=("微软雅黑", 9)
                           ).pack(side=tk.LEFT, padx=(4, 0))

        self.history_button = tk.Menubutton(
            row, text="🕐 历史 ▾", bg=BG_HOVER, fg=FG_PRIMARY,
            relief=tk.FLAT, font=("微软雅黑", 9, "bold"), padx=8, pady=3,
            cursor="hand2", activebackground=BG_HOVER,
        )
        self.history_button.pack(side=tk.RIGHT)
        self.history_menu = tk.Menu(self.history_button, tearoff=0,
                                    bg=BG_CARD, fg=FG_PRIMARY,
                                    activebackground="#585b70", relief=tk.FLAT)
        self.history_button.config(menu=self.history_menu)
        self.history_menu.add_command(label="（暂无历史记录）", state=tk.DISABLED)

    def _build_custom_input(self):
        row = tk.Frame(self.frame, bg=BG_SURFACE)
        row.pack(fill=tk.X)
        tk.Label(row, text="自定义指令:", bg=BG_SURFACE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self.custom_var, bg=BG_CARD, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief=tk.FLAT, font=("微软雅黑", 9)
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(8, 0))


class ActionBar:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=BG_BASE)
        self.frame.pack(fill=tk.X, padx=12, pady=(0, 6))

    def add_group(self, title):
        group = tk.Frame(self.frame, bg=BG_SURFACE, padx=8, pady=8)
        group.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        tk.Label(group, text=title, bg=BG_SURFACE, fg=FG_MUTED,
                 font=("微软雅黑", 8, "bold")).pack(anchor="w", pady=(0, 6))
        row = tk.Frame(group, bg=BG_SURFACE)
        row.pack(fill=tk.X)
        return row

    def action_button(self, parent, text, command, color, state=tk.NORMAL, tip=""):
        button = tk.Button(parent, text=text, command=command,
                           bg=color, fg=DARK_TEXT, relief=tk.FLAT,
                           font=("微软雅黑", 9, "bold"), padx=8, pady=3,
                           cursor="hand2", activebackground=color, state=state)
        button.pack(side=tk.LEFT, padx=(0, 4))
        if tip:
            Tooltip(button, tip)
        return button


class ResultPanel:
    @staticmethod
    def build_header(parent, diff_var, on_toggle_diff, on_copy_result):
        header = tk.Frame(parent, bg=BG_BASE)
        header.pack(fill=tk.X)
        tk.Label(header, text="AI 优化结果", bg=BG_BASE, fg=ACCENT_GREEN,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        diff_cb = tk.Checkbutton(header, text="差异高亮", variable=diff_var,
                                 bg=BG_BASE, fg=FG_MUTED, activebackground=BG_BASE,
                                 selectcolor=BG_CARD, font=("微软雅黑", 8),
                                 command=on_toggle_diff)
        diff_cb.pack(side=tk.LEFT, padx=(10, 0))
        Tooltip(diff_cb, "差异高亮\n绿色 = 新增的词，红色删除线 = 被移除的词。")
        copy_btn = tk.Button(header, text="📋 复制结果", command=on_copy_result,
                             bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
                             font=("微软雅黑", 8), padx=8, pady=1,
                             cursor="hand2", activebackground=BG_HOVER)
        copy_btn.pack(side=tk.RIGHT)
        Tooltip(copy_btn, "📋 复制结果\n直接将右侧 AI 结果复制到剪贴板。")
        return header


class InsightsPanel:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=BG_BASE)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(self.frame, text="Insights / 结果辅助", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 8, "bold")).pack(anchor="w", padx=12, pady=(4, 0))

    @staticmethod
    def build_keywords(frame, keywords, on_copy, on_close):
        _clear_and_show(frame)
        header = _header(frame, "🏷 关键词（点击复制）:", FG_MUTED, on_close)
        header.pack(fill=tk.X)
        rows_needed = (len(keywords) + 7) // 8
        for row_index in range(rows_needed):
            row = tk.Frame(frame, bg=BG_BASE)
            row.pack(fill=tk.X, pady=(2, 0))
            for keyword in keywords[row_index * 8: (row_index + 1) * 8]:
                tk.Button(
                    row, text=keyword, bg=ACCENT_BLUE, fg=DARK_TEXT,
                    relief=tk.FLAT, font=("微软雅黑", 8), padx=8, pady=3,
                    cursor="hand2", activebackground=ACCENT_BLUE,
                    command=lambda value=keyword: on_copy(value),
                ).pack(side=tk.LEFT, padx=(0, 4))

    @staticmethod
    def build_negative_recommendations(frame, groups, on_copy, on_copy_all, on_close):
        _clear_and_show(frame)
        header = _header(frame, "🚫 推荐负面词（点击复制）:", ACCENT_RED, on_close)
        header.pack(fill=tk.X)
        all_words = [word for _, words in groups for word in words]
        if all_words:
            tk.Button(header, text="📋 全部复制", command=lambda: on_copy_all(all_words),
                      bg=ACCENT_RED, fg=DARK_TEXT, relief=tk.FLAT,
                      font=("微软雅黑", 8, "bold"), padx=8, pady=1,
                      cursor="hand2", activebackground=ACCENT_RED).pack(side=tk.RIGHT, padx=(0, 4))

        group_colors = [ACCENT_RED, ACCENT_ORANGE, ACCENT_YELLOW]
        for group_index, (group_label, words) in enumerate(groups):
            row = tk.Frame(frame, bg=BG_BASE)
            row.pack(fill=tk.X, pady=(4, 0))
            tk.Label(row, text=f"  {group_label}:", bg=BG_BASE,
                     fg=group_colors[group_index % len(group_colors)],
                     font=("微软雅黑", 8, "bold")).pack(side=tk.LEFT)
            for word in words:
                tk.Button(
                    row, text=word, bg=BG_CARD, fg=ACCENT_RED,
                    relief=tk.FLAT, font=("微软雅黑", 8), padx=6, pady=2,
                    cursor="hand2", activebackground=BG_HOVER,
                    command=lambda value=word: on_copy(value),
                ).pack(side=tk.LEFT, padx=(2, 2))


def _clear_and_show(frame):
    for widget in frame.winfo_children():
        widget.destroy()
    frame.pack(fill=tk.X, padx=12, pady=(2, 4))


def _header(parent, title, color, on_close):
    header = tk.Frame(parent, bg=BG_BASE)
    tk.Label(header, text=title, bg=BG_BASE, fg=color,
             font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
    tk.Button(header, text="✕ 关闭", command=on_close,
              bg=BG_HOVER, fg=FG_MUTED, relief=tk.FLAT,
              font=("微软雅黑", 8), padx=4, pady=0,
              cursor="hand2", activebackground=BG_HOVER).pack(side=tk.RIGHT)
    return header
