"""
主窗口 PromptTool：Prompt 列表管理 + 编辑区 + 工具栏
"""
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.simpledialog
import pyperclip

from app.layout import MainLayoutSpec
from core.services.prompt_service import PromptService
from infrastructure.json_prompt_store import JsonPromptStore
from shared.storage import DATA_FILE
from shared.ui_kit import (
    bind_mousewheel, Tooltip,
    BG_BASE, BG_ELEVATED, BG_SURFACE, BG_CARD, BG_HOVER, BORDER_SUBTLE,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_YELLOW,
    ACCENT_RED, ACCENT_CYAN, ACCENT_ORANGE, DARK_TEXT,
    FONT_FAMILY,
)
from features.camera_builder.widget import CameraBuilder
from features.ai_optimize.widget   import AIOptimizeDialog
from features.ai_settings.widget   import AISettingsDialog


class PromptTool(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Prompt Studio")
        self.geometry("1040x680")
        self.minsize(960, 620)
        self.configure(bg=BG_BASE)
        self.resizable(True, True)

        self.prompt_store    = JsonPromptStore(DATA_FILE)
        self.prompt_service  = PromptService(self.prompt_store)
        self.prompts         = self.prompt_service.prompts
        self.selected_index  = None
        self.checked_indices = self.prompt_service.checked_indices
        self.check_vars      = {}
        self.action_buttons  = {}
        self.compact_mode    = False
        self.topmost_mode    = False
        self.layout_spec     = MainLayoutSpec.default()

        self._build_ui()
        self._sync_prompts()
        self._refresh_buttons()

    # ─────────────────────────────────────────────────────────────
    #  UI 骨架
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        shell = tk.Frame(self, bg=BG_BASE)
        shell.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        toolbar = tk.Frame(shell, bg=BG_ELEVATED, padx=12, pady=9,
                           highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        toolbar.pack(fill=tk.X)
        brand = tk.Frame(toolbar, bg=BG_ELEVATED)
        brand.pack(side=tk.LEFT)
        tk.Label(brand, text="Prompt Studio", bg=BG_ELEVATED, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 12, "bold")).pack(anchor="w")
        tk.Label(brand, text="AI Command Center · Local Workspace", bg=BG_ELEVATED, fg=FG_DIM,
                 font=(FONT_FAMILY, 8)).pack(anchor="w", pady=(1, 0))

        self.topmost_btn = self._btn(toolbar, "📌 置顶",     self._toggle_topmost,      ACCENT_YELLOW)
        self.topmost_btn.pack(side=tk.RIGHT, padx=(6, 0))
        Tooltip(self.topmost_btn, "📌 置顶\n让窗口始终显示在所有其他窗口上方，方便对照使用。")
        self.compact_btn = self._btn(toolbar, "🗂 精简模式", self._toggle_compact_mode, "#94e2d5")
        self.compact_btn.pack(side=tk.RIGHT)
        Tooltip(self.compact_btn, "🗂 精简模式\n收起主窗口，弹出一个迷你浮动列表，可拖动放置在屏幕任意位置，便于随时复制 Prompt。")
        settings_btn = self._btn(toolbar, "⚙ 设置", self._ai_settings, BG_HOVER)
        settings_btn.config(fg=FG_PRIMARY)
        settings_btn.pack(side=tk.RIGHT, padx=(0, 6))
        Tooltip(settings_btn, "⚙ 设置\n配置 AI 服务的 API Key、模型和接口地址。")
        help_btn = self._btn(toolbar, "❓ 帮助", self._open_help, BG_HOVER)
        help_btn.config(fg=FG_PRIMARY)
        help_btn.pack(side=tk.RIGHT, padx=(0, 6))
        Tooltip(help_btn, "❓ 帮助\n查看完整使用说明和功能介绍。")

        workbench = tk.Frame(shell, bg=BG_BASE)
        workbench.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        workbench.grid_columnconfigure(0, weight=2, minsize=260)
        workbench.grid_columnconfigure(1, weight=5, minsize=420)
        workbench.grid_columnconfigure(2, weight=2, minsize=230)
        workbench.grid_rowconfigure(0, weight=1)

        self.left_pane  = tk.Frame(workbench, bg=BG_ELEVATED, padx=10, pady=10,
                                   highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        self.right_pane = tk.Frame(workbench, bg=BG_ELEVATED, padx=10, pady=10,
                                   highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        self.tools_pane = tk.Frame(workbench, bg=BG_ELEVATED, padx=10, pady=10,
                                   highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        self.left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.right_pane.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        self.tools_pane.grid(row=0, column=2, sticky="nsew")

        self._build_left_pane()
        self._build_right_pane()
        self._build_tools_pane()

    def _build_left_pane(self):
        header = tk.Frame(self.left_pane, bg=BG_ELEVATED)
        header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(header, text="Outliner", bg=BG_ELEVATED, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 11, "bold")).pack(side=tk.LEFT)
        self.library_status_label = tk.Label(header, text="", bg=BG_ELEVATED,
                                             fg=FG_MUTED, font=(FONT_FAMILY, 8))
        self.library_status_label.pack(side=tk.RIGHT)

        # 搜索框
        self.search_var = tk.StringVar()
        self._search_entry = tk.Entry(self.left_pane, textvariable=self.search_var,
                                      bg=BG_CARD, fg=FG_DIM,
                                      insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                      font=(FONT_FAMILY, 9))
        self._search_entry.pack(fill=tk.X, ipady=6, pady=(0, 8))
        self._search_entry.insert(0, "Search")
        self.search_var.trace_add("write", lambda *_: self._refresh_buttons())
        self._search_entry.bind("<FocusIn>",  self._search_focus_in)
        self._search_entry.bind("<FocusOut>", self._search_focus_out)

        # 列表区（带滚动）
        list_frame = tk.Frame(self.left_pane, bg=BG_ELEVATED)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(list_frame, bg=BG_ELEVATED, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self._canvas.yview)
        self.btn_frame = tk.Frame(self._canvas, bg=BG_ELEVATED)
        self.btn_frame.bind("<Configure>",
                            lambda _e: self._canvas.configure(
                                scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self.btn_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        bind_mousewheel(self._canvas)

        # 操作按钮组
        action_frame = tk.Frame(self.left_pane, bg=BG_ELEVATED)
        action_frame.pack(fill=tk.X, pady=(8, 0))

        def _group(title):
            box = tk.Frame(action_frame, bg=BG_SURFACE, padx=8, pady=8,
                           highlightbackground=BORDER_SUBTLE, highlightthickness=1)
            box.pack(fill=tk.X, pady=(0, 7))
            tk.Label(box, text=title, bg=BG_SURFACE, fg=FG_MUTED,
                     font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(0, 6))
            row = tk.Frame(box, bg=BG_SURFACE)
            row.pack(fill=tk.X)
            return row

        r1 = _group("主要操作")
        b_new = self._btn(r1, "+ 新建",  self._new_prompt,    ACCENT_GREEN )
        b_new.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_new, "+ 新建\n创建一个新的空白 Prompt 条目，自动进入编辑模式。")
        b_edit = self._btn(r1, "✎ 编辑",  self._edit_prompt,   ACCENT_BLUE  )
        b_edit.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["edit"] = b_edit
        Tooltip(b_edit, "✎ 编辑\n选中一条 Prompt 后点击，进入编辑模式，可修改标题和内容。编辑完成后点[保存]。")
        b_del = self._btn(r1, "✕ 删除",  self._delete_prompt, ACCENT_RED   )
        b_del.pack(side=tk.LEFT)
        self.action_buttons["delete"] = b_del
        Tooltip(b_del, "✕ 删除\n删除当前选中的 Prompt（不可撤销，会弹出确认对话框）。")

        r2 = _group("排序")
        b_up = self._btn(r2, "↑ 上移", lambda: self._move(-1), ACCENT_ORANGE)
        b_up.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["move_up"] = b_up
        Tooltip(b_up, "↑ 上移\n将当前选中的 Prompt 在列表中向上移动一位，调整排列顺序。")
        b_dn = self._btn(r2, "↓ 下移", lambda: self._move(1),  ACCENT_ORANGE)
        b_dn.pack(side=tk.LEFT)
        self.action_buttons["move_down"] = b_dn
        Tooltip(b_dn, "↓ 下移\n将当前选中的 Prompt 在列表中向下移动一位，调整排列顺序。")

        r3 = _group("批量")
        b_copy_checked = self._btn(r3, "☑ 拼接复制", self._copy_checked_prompts,  ACCENT_CYAN  )
        b_copy_checked.pack(side=tk.TOP, anchor="w", fill=tk.X, pady=(0, 4))
        self.action_buttons["copy_checked"] = b_copy_checked
        Tooltip(b_copy_checked, "☑ 拼接复制\n将所有勾选的 Prompt 内容拼接（用空行分隔），一次性复制到剪贴板，适合组合使用多个 Prompt。")
        batch_row = tk.Frame(r3, bg=BG_SURFACE)
        batch_row.pack(fill=tk.X)
        b_selall = self._btn(batch_row, "全选",        self._select_all_prompts,    "#74c7ec"    )
        b_selall.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_selall, "全选\n勾选列表中的所有 Prompt。")
        b_clrsel = self._btn(batch_row, "清空选择",    self._clear_checked_prompts, "#9399b2"    )
        b_clrsel.pack(side=tk.LEFT)
        Tooltip(b_clrsel, "清空选择\n取消所有 Prompt 的勾选状态。")

    def _build_right_pane(self):
        header = tk.Frame(self.right_pane, bg=BG_ELEVATED)
        header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(header, text="Canvas", bg=BG_ELEVATED, fg=FG_DIM,
                 font=(FONT_FAMILY, 8, "bold")).pack(side=tk.RIGHT)
        self.edit_mode_label = tk.Label(header, text="未选择 Prompt", bg=BG_ELEVATED, fg=FG_PRIMARY,
                                        font=(FONT_FAMILY, 11, "bold"))
        self.edit_mode_label.pack(side=tk.LEFT)

        title_frame = tk.Frame(self.right_pane, bg=BG_ELEVATED)
        title_frame.pack(fill=tk.X, pady=(0, 6))
        tk.Label(title_frame, text="标题:", bg=BG_ELEVATED, fg=FG_MUTED,
                 font=(FONT_FAMILY, 9)).pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(title_frame, textvariable=self.title_var,
                                    bg=BG_CARD, fg=FG_PRIMARY,
                                    insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                    font=(FONT_FAMILY, 10), state=tk.DISABLED,
                                    disabledbackground=BG_SURFACE, disabledforeground=FG_DIM)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(6, 0))

        self.ghost_node_canvas = tk.Canvas(
            self.right_pane, height=150, bg=BG_BASE,
            highlightthickness=1, highlightbackground=BORDER_SUBTLE,
        )
        self.ghost_node_canvas.pack(fill=tk.X, pady=(0, 8))
        self._draw_ghost_mindmap()

        self.text_area = tk.Text(self.right_pane, bg=BG_SURFACE, fg=FG_MUTED,
                                 insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                 font=(FONT_FAMILY, 10), wrap=tk.WORD, padx=12, pady=12,
                                 state=tk.DISABLED)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        right_bottom = tk.Frame(self.right_pane, bg=BG_ELEVATED)
        right_bottom.pack(fill=tk.X, pady=(8, 0))
        b_save = self._btn(right_bottom, "💾 保存",          self._save_edit,     ACCENT_GREEN )
        b_save.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["save"] = b_save
        Tooltip(b_save, "💾 保存\n将编辑区的标题和内容保存到本地文件中（JSON 格式，重启后仍保留）。")
        b_copy = self._btn(right_bottom, "📋 复制到剪切板",  self._copy_current,  ACCENT_CYAN  )
        b_copy.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["copy_current"] = b_copy
        Tooltip(b_copy, "📋 复制到剪切板\n将右侧编辑区中的 Prompt 内容复制到剪贴板，可直接粘贴到 AI 生图工具中使用。")

        self.status_label = tk.Label(right_bottom, text="", bg=BG_ELEVATED,
                                     fg=ACCENT_GREEN, font=(FONT_FAMILY, 9))
        self.status_label.pack(side=tk.LEFT, padx=10)

    def _build_tools_pane(self):
        tk.Label(self.tools_pane, text="Inspector", bg=BG_ELEVATED, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(self.tools_pane, text="核心入口", bg=BG_ELEVATED, fg=ACCENT_BLUE,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(0, 6))

        intro = tk.Label(
            self.tools_pane,
            text="最常用的两个动作放在这里：先生成 Prompt，再对当前 Prompt 做 AI 优化。",
            bg=BG_ELEVATED,
            fg=FG_MUTED,
            font=(FONT_FAMILY, 8),
            justify=tk.LEFT,
            wraplength=220,
        )
        intro.pack(anchor="w", fill=tk.X, pady=(0, 10))

        hero = tk.Frame(self.tools_pane, bg=BG_ELEVATED)
        hero.pack(fill=tk.X, pady=(0, 12))

        def _hero_entry(title, desc, action_text, command, color, key=None):
            card = tk.Frame(hero, bg=BG_SURFACE, padx=12, pady=12,
                            highlightbackground=color, highlightthickness=1)
            card.pack(fill=tk.X, pady=(0, 8))
            tk.Label(card, text=title, bg=BG_SURFACE, fg=color,
                     font=(FONT_FAMILY, 11, "bold")).pack(anchor="w")
            tk.Label(card, text=desc, bg=BG_SURFACE, fg=FG_MUTED,
                     font=(FONT_FAMILY, 8), justify=tk.LEFT,
                     wraplength=205).pack(anchor="w", fill=tk.X, pady=(4, 10))
            btn = tk.Button(card, text=action_text, command=command,
                            bg=BG_CARD, fg=color, relief=tk.FLAT,
                            font=(FONT_FAMILY, 9, "bold"), padx=12, pady=5,
                            activebackground=BG_HOVER, cursor="hand2",
                            highlightbackground=color, highlightthickness=1)
            btn.pack(fill=tk.X)
            if key:
                self.action_buttons[key] = btn
            return card

        _hero_entry(
            "✨ 生成新 Prompt",
            "打开提示词生成器：场景、风格、镜头、输出四步生成，完成后直接插入列表。",
            "打开提示词生成器",
            self._open_camera_builder,
            ACCENT_GREEN,
            key="builder",
        )
        _hero_entry(
            "🤖 优化当前 Prompt",
            "选择左侧 Prompt 后，可优化、翻译、扩写、评分、合规修复或生成变体。",
            "AI 优化当前 Prompt",
            self._ai_optimize,
            ACCENT_PURPLE,
            key="ai_optimize",
        )

        tk.Label(self.tools_pane, text="辅助", bg=BG_ELEVATED, fg=FG_MUTED,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(4, 6))

        def _tool_card(title, desc, action_text, command, color):
            card = tk.Frame(self.tools_pane, bg=BG_SURFACE, padx=10, pady=10,
                            highlightbackground=BORDER_SUBTLE, highlightthickness=1)
            card.pack(fill=tk.X, pady=(0, 8))
            tk.Label(card, text=title, bg=BG_SURFACE, fg=FG_PRIMARY,
                     font=(FONT_FAMILY, 9, "bold")).pack(anchor="w")
            tk.Label(card, text=desc, bg=BG_SURFACE, fg=FG_MUTED,
                     font=(FONT_FAMILY, 8), justify=tk.LEFT,
                     wraplength=210).pack(anchor="w", fill=tk.X, pady=(4, 8))
            btn = self._btn(card, action_text, command, color)
            btn.pack(anchor="e")
            return card

        _tool_card(
            "⚙ AI 设置",
            "配置 API Key、模型和兼容接口地址。",
            "配置",
            self._ai_settings,
            BG_HOVER,
        )
        _tool_card(
            "❓ 帮助",
            "查看功能说明和常见操作提示。",
            "查看",
            self._open_help,
            BG_HOVER,
        )

    # ─────────────────────────────────────────────────────────────
    #  工具函数
    # ─────────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, color=ACCENT_BLUE):
        return tk.Button(parent, text=text, command=cmd,
                         bg=BG_CARD, fg=color, relief=tk.FLAT,
                         font=(FONT_FAMILY, 9, "bold"), padx=10, pady=4,
                         activebackground=BG_HOVER, cursor="hand2",
                         highlightbackground=color, highlightthickness=1)

    def _ghost_node(self, canvas, x, y, text, accent=ACCENT_BLUE, w=118):
        canvas.create_rectangle(
            x, y, x + w, y + 34,
            fill=BG_SURFACE, outline=BORDER_SUBTLE, width=1,
        )
        canvas.create_line(x, y + 17, x + 4, y + 17, fill=accent, width=3)
        canvas.create_text(
            x + 14, y + 17, text=text, anchor="w",
            fill=FG_PRIMARY, font=(FONT_FAMILY, 8, "bold"),
        )

    def _draw_ghost_mindmap(self):
        canvas = self.ghost_node_canvas
        canvas.delete("all")
        canvas.create_text(
            16, 14, text="RELEASE TO CREATE NEW", anchor="w",
            fill=FG_DIM, font=(FONT_FAMILY, 7, "bold"),
        )
        self._ghost_node(canvas, 24, 58, "Prompt", ACCENT_BLUE, 100)
        self._ghost_node(canvas, 176, 30, "Generate", ACCENT_GREEN, 116)
        self._ghost_node(canvas, 176, 88, "Optimize", ACCENT_PURPLE, 116)
        self._ghost_node(canvas, 334, 58, "Publish", ACCENT_CYAN, 104)
        canvas.create_line(124, 75, 176, 47, fill=BORDER_SUBTLE, width=2, smooth=True)
        canvas.create_line(124, 75, 176, 105, fill=BORDER_SUBTLE, width=2, smooth=True)
        canvas.create_line(292, 47, 334, 75, fill=BORDER_SUBTLE, width=2, smooth=True)
        canvas.create_line(292, 105, 334, 75, fill=BORDER_SUBTLE, width=2, smooth=True)
        canvas.create_oval(120, 71, 128, 79, fill=ACCENT_BLUE, outline="")
        canvas.create_oval(330, 71, 338, 79, fill=ACCENT_CYAN, outline="")

    def _flash_status(self, msg):
        self.status_label.config(text=msg)
        self.after(2000, lambda: self.status_label.config(text=""))

    def _sync_prompts(self):
        self.prompts = self.prompt_service.prompts
        self.checked_indices = self.prompt_service.checked_indices
        self._refresh_library_status()
        self._refresh_empty_state()
        self._refresh_action_states()

    def _refresh_library_status(self):
        if not hasattr(self, "library_status_label"):
            return
        status = self.prompt_service.status_summary(self.selected_index)
        selected = "已选择" if status["selected"] else "未选择"
        self.library_status_label.config(
            text=f"{status['total']} 条 / 勾选 {status['checked']} / {selected}"
        )

    def _refresh_action_states(self):
        if not self.action_buttons:
            return
        state = self.prompt_service.action_state(self.selected_index)
        mapping = {
            "edit": state["can_edit"],
            "delete": state["can_delete"],
            "move_up": state["can_move_up"],
            "move_down": state["can_move_down"],
            "copy_checked": state["can_copy_checked"],
            "save": state["can_edit"],
            "copy_current": state["can_edit"],
            "ai_optimize": state["can_ai_optimize"],
        }
        for key, enabled in mapping.items():
            if key in self.action_buttons:
                self.action_buttons[key].config(
                    state=tk.NORMAL if enabled else tk.DISABLED
                )

    def _refresh_empty_state(self):
        if not hasattr(self, "text_area") or self.selected_index is not None:
            return
        message = (
            "还没有 Prompt。\n\n点击左侧「+ 新建」创建第一条 Prompt，"
            "或打开右侧「提示词生成器」。"
            if not self.prompts else
            "请从左侧 Prompt 库选择一条内容，或点击「+ 新建」。"
        )
        self.text_area.config(state=tk.NORMAL, bg=BG_SURFACE, fg=FG_DIM)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", message)
        self.text_area.config(state=tk.DISABLED)

    def _set_edit_mode(self, editable: bool):
        state = tk.NORMAL if editable else tk.DISABLED
        self.text_area.config(state=state,
                              bg=BG_CARD if editable else BG_SURFACE,
                              fg=FG_PRIMARY if editable else FG_MUTED)
        self.title_entry.config(state=state)
        self.edit_mode_label.config(
            text="编辑中..." if editable else self._preview_title()
        )
        self._refresh_action_states()

    def _preview_title(self):
        return "预览当前 Prompt" if self.selected_index is not None else "未选择 Prompt"

    # ─────────────────────────────────────────────────────────────
    #  搜索栏
    # ─────────────────────────────────────────────────────────────
    def _search_focus_in(self, _e):
        if self._search_entry.get() == "Search":
            self._search_entry.delete(0, tk.END)
            self._search_entry.config(fg=FG_PRIMARY)

    def _search_focus_out(self, _e):
        if not self._search_entry.get():
            self._search_entry.insert(0, "Search")
            self._search_entry.config(fg=FG_DIM)

    # ─────────────────────────────────────────────────────────────
    #  列表刷新
    # ─────────────────────────────────────────────────────────────
    def _refresh_buttons(self):
        for w in self.btn_frame.winfo_children():
            w.destroy()
        self.check_vars.clear()

        visible_indices = self.prompt_service.search(self.search_var.get())

        for i in visible_indices:
            p = self.prompts[i]

            row_bg = BG_HOVER if i == self.selected_index else BG_ELEVATED
            row = tk.Frame(self.btn_frame, bg=row_bg)
            row.pack(fill=tk.X, pady=2)
            tk.Frame(row, bg=ACCENT_BLUE if i == self.selected_index else row_bg,
                     width=3).pack(side=tk.LEFT, fill=tk.Y)

            checked = tk.BooleanVar(value=i in self.checked_indices)
            self.check_vars[i] = checked
            tk.Checkbutton(row, variable=checked,
                           bg=row.cget("bg"), activebackground=row.cget("bg"),
                           selectcolor=BG_CARD, fg=FG_PRIMARY,
                           relief=tk.FLAT, highlightthickness=0, bd=0,
                           command=lambda idx=i: self._toggle_check(idx)
                           ).pack(side=tk.LEFT, padx=(6, 4))

            label = p.display_label()
            btn = tk.Button(row, text=label, anchor="w",
                            bg=row.cget("bg"), fg=FG_PRIMARY, relief=tk.FLAT,
                            font=("微软雅黑", 9), padx=8, pady=6,
                            activebackground="#585b70", cursor="hand2",
                            command=lambda idx=i: self._select(idx))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            btn.bind("<Button-3>", lambda e, idx=i: self._context_menu(e, idx))

    # ─────────────────────────────────────────────────────────────
    #  多选操作
    # ─────────────────────────────────────────────────────────────
    def _toggle_check(self, index):
        self.prompt_service.toggle_checked(index)
        self._sync_prompts()
        if index in self.check_vars:
            self.check_vars[index].set(index in self.checked_indices)

    def _copy_checked_prompts(self):
        content = self.prompt_service.join_checked_contents()
        if not content:
            messagebox.showinfo("提示", "请先勾选至少一个 Prompt")
            return
        pyperclip.copy(content)
        self._flash_status(f"已拼接复制 {len(self.checked_indices)} 条 ✓")

    def _select_all_prompts(self):
        self.prompt_service.select_all()
        self._sync_prompts()
        self._refresh_buttons()
        self._flash_status("已全选 ✓")

    def _clear_checked_prompts(self):
        self.prompt_service.clear_checked()
        self._sync_prompts()
        self._refresh_buttons()
        self._flash_status("已清空选择 ✓")

    # ─────────────────────────────────────────────────────────────
    #  单条选择 / CRUD
    # ─────────────────────────────────────────────────────────────
    def _select(self, index):
        self.selected_index = index
        self._sync_prompts()
        p = self.prompts[index]
        self._set_edit_mode(False)
        self.title_var.set(p.title)
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", p.content)
        self.text_area.config(state=tk.DISABLED)
        pyperclip.copy(p.content)
        self._flash_status("已复制到剪切板 ✓")
        self._refresh_buttons()

    def _new_prompt(self):
        idx = self.prompt_service.add_prompt(title="新 Prompt", content="")
        self.selected_index = idx
        self._sync_prompts()
        self._set_edit_mode(True)
        self.title_var.set("新 Prompt")
        self.text_area.delete("1.0", tk.END)
        self._refresh_buttons()
        self.title_entry.focus_set()
        self.title_entry.select_range(0, tk.END)

    def _edit_prompt(self):
        if self.selected_index is None:
            messagebox.showinfo("提示", "请先选择一个 Prompt")
            return
        self._set_edit_mode(True)
        self.text_area.focus_set()

    def _save_edit(self):
        if self.selected_index is None:
            messagebox.showinfo("提示", "请先选择一个 Prompt 再保存")
            return
        title   = self.title_var.get().strip() or "未命名"
        content = self.text_area.get("1.0", tk.END).rstrip()
        self.prompt_service.update_prompt(self.selected_index, title, content)
        self._sync_prompts()
        self._set_edit_mode(False)
        self._refresh_buttons()
        self._flash_status("已保存 ✓")

    def _delete_prompt(self):
        if self.selected_index is None:
            messagebox.showinfo("提示", "请先选择一个 Prompt")
            return
        title = self.prompts[self.selected_index].title
        if not messagebox.askyesno("确认删除", f"确定要删除「{title}」吗？此操作不可撤销。"):
            return
        deleted_index = self.selected_index
        self.prompt_service.delete_prompt(deleted_index)
        if self.prompts:
            self.selected_index = min(deleted_index, len(self.prompts) - 1)
            self._select(self.selected_index)
        else:
            self.selected_index = None
            self._sync_prompts()
            self._set_edit_mode(False)
            self.title_var.set("")
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(state=tk.DISABLED)
            self._refresh_buttons()
        self._refresh_buttons()

    def _move(self, direction):
        if self.selected_index is None:
            messagebox.showinfo("提示", "请先选择一个 Prompt")
            return
        i = self.selected_index
        j = self.prompt_service.move_prompt(i, direction)
        if j == i:
            self._flash_status("已经到边界了")
            return
        self.selected_index = j
        self._sync_prompts()
        self._refresh_buttons()

    def _copy_current(self):
        if self.selected_index is None:
            messagebox.showinfo("提示", "请先选择一个 Prompt")
            return
        self.text_area.config(state=tk.NORMAL)
        content = self.text_area.get("1.0", tk.END).strip()
        editing = self.edit_mode_label.cget("text") == "编辑中..."
        if not editing:
            self.text_area.config(state=tk.DISABLED)
        if content:
            pyperclip.copy(content)
            self._flash_status("已复制到剪切板 ✓")

    def _context_menu(self, event, index):
        menu = tk.Menu(self, tearoff=0, bg=BG_CARD, fg=FG_PRIMARY,
                       activebackground="#585b70", relief=tk.FLAT)
        menu.add_command(label="复制内容",
                         command=lambda: self._select(index))
        menu.add_command(label="编辑",
                         command=lambda: (self._select(index), self._edit_prompt()))
        menu.add_separator()
        menu.add_command(label="删除",
                         command=lambda: (
                             setattr(self, "selected_index", index),
                             self._delete_prompt()))
        menu.tk_popup(event.x_root, event.y_root)

    # ─────────────────────────────────────────────────────────────
    #  精简模式 / 置顶
    # ─────────────────────────────────────────────────────────────
    def _toggle_compact_mode(self):
        self.compact_mode = not self.compact_mode
        if self.compact_mode:
            self.withdraw()
            self._open_compact_overlay()
        else:
            self.deiconify()
            self.compact_btn.config(text="🗂 精简模式")

    def _open_compact_overlay(self):
        ov = tk.Toplevel(self)
        ov.overrideredirect(True)
        ov.attributes("-topmost", True)
        ov.configure(bg=BG_BASE)
        # Position near the compact mode button (top-right area)
        self.update_idletasks()
        bx = self.compact_btn.winfo_rootx()
        by = self.compact_btn.winfo_rooty()
        bh = self.compact_btn.winfo_height()
        ov.geometry(f"220x600+{bx}+{by + bh + 4}")
        self._compact_win = ov

        ov._drag_x = ov._drag_y = 0
        def _on_press(e):
            ov._drag_x = e.x_root - ov.winfo_x()
            ov._drag_y = e.y_root - ov.winfo_y()
        def _on_drag(e):
            ov.geometry(f"+{e.x_root - ov._drag_x}+{e.y_root - ov._drag_y}")

        bar = tk.Frame(ov, bg=BG_CARD, height=24)
        bar.pack(fill=tk.X)
        bar.bind("<Button-1>", _on_press)
        bar.bind("<B1-Motion>", _on_drag)
        lbl = tk.Label(bar, text="Prompts  ·  拖动移动", bg=BG_CARD, fg=FG_MUTED,
                       font=("微软雅黑", 8))
        lbl.pack(side=tk.LEFT, padx=6)
        lbl.bind("<Button-1>", _on_press)
        lbl.bind("<B1-Motion>", _on_drag)
        tk.Button(bar, text="↔ 恢复", command=self._exit_compact,
                  bg=ACCENT_GREEN, fg=DARK_TEXT, relief=tk.FLAT,
                  font=("微软雅黑", 8, "bold"), padx=6, pady=0,
                  cursor="hand2", activebackground=ACCENT_GREEN).pack(side=tk.RIGHT, padx=2, pady=2)

        list_frame = tk.Frame(ov, bg=BG_BASE)
        list_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(list_frame, bg=BG_BASE, highlightthickness=0)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_BASE)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        bind_mousewheel(canvas)
        self._compact_list_inner = inner
        self._refresh_compact_list()

    def _refresh_compact_list(self):
        if not hasattr(self, "_compact_list_inner") or \
                not self._compact_list_inner.winfo_exists():
            return
        inner = self._compact_list_inner
        for w in inner.winfo_children():
            w.destroy()
        for i, p in enumerate(self.prompts):
            label = p.display_label(18)
            tk.Button(inner, text=label, anchor="w",
                      bg=BG_HOVER if i == self.selected_index else BG_SURFACE,
                      fg=FG_PRIMARY, relief=tk.FLAT,
                      font=("微软雅黑", 9), padx=8, pady=5,
                      activebackground="#585b70", cursor="hand2",
                      command=lambda idx=i: self._compact_select(idx)
                      ).pack(fill=tk.X, pady=1, padx=2)

    def _compact_select(self, index):
        self._select(index)
        self._refresh_compact_list()

    def _exit_compact(self):
        self.compact_mode = False
        if hasattr(self, "_compact_win") and self._compact_win.winfo_exists():
            self._compact_win.destroy()
        self.deiconify()
        self.compact_btn.config(text="🗂 精简模式")

    def _toggle_topmost(self):
        self.topmost_mode = not self.topmost_mode
        self.attributes("-topmost", self.topmost_mode)
        self.topmost_btn.config(
            text="📍 取消置顶" if self.topmost_mode else "📌 置顶")

    # ─────────────────────────────────────────────────────────────
    #  摄影机构建器
    # ─────────────────────────────────────────────────────────────
    def _open_camera_builder(self):
        CameraBuilder(self, on_insert=self._insert_from_builder)

    def _insert_from_builder(self, title, content):
        self.prompt_service.add_prompt(title=title, content=content)
        self._sync_prompts()
        self._select(len(self.prompts) - 1)
        self._flash_status(f"「{title}」已插入列表 ✓")

    # ─────────────────────────────────────────────────────────────
    #  AI 功能
    # ─────────────────────────────────────────────────────────────
    def _ai_settings(self):
        AISettingsDialog(self)

    def _open_help(self):
        from features.help.widget import HelpDialog
        HelpDialog(self)

    def _ai_optimize(self):
        if self.selected_index is None:
            messagebox.showinfo("提示", "请先选择一个 Prompt")
            return
        self.text_area.config(state=tk.NORMAL)
        current = self.text_area.get("1.0", tk.END).strip()
        editing = self.edit_mode_label.cget("text") == "编辑中..."
        if not editing:
            self.text_area.config(state=tk.DISABLED)
        if not current:
            messagebox.showinfo("提示", "当前 Prompt 为空，请先输入内容")
            return

        def _on_apply(result):
            self._set_edit_mode(True)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", result)
            self._flash_status("AI 优化结果已应用，请确认后保存 ✓")

        def _on_saveas(result):
            title = tkinter.simpledialog.askstring(
                "另存为 Prompt", "请输入新 Prompt 的标题：",
                initialvalue=self.prompts[self.selected_index].title + " (AI优化)",
            )
            if title is None:
                return
            self.prompt_service.add_prompt(title=title.strip() or "AI优化结果", content=result)
            self._sync_prompts()
            self._refresh_buttons()
            self._flash_status(f"「{title.strip()}」已另存为新 Prompt ✓")

        AIOptimizeDialog(self, current_prompt=current,
                         on_apply=_on_apply, on_saveas=_on_saveas)
