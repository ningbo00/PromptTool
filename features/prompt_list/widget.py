"""
主窗口 PromptTool：Prompt 列表管理 + 编辑区 + 工具栏
"""
from shared import qt_compat as tk
from shared.qt_compat import messagebox, simpledialog, ttk
import pyperclip

import shared.config as cfg
from app.layout import MainLayoutSpec
from core.services.prompt_service import PromptService
from infrastructure.json_prompt_store import JsonPromptStore
from shared.storage import DATA_FILE
from shared.global_hotkeys import global_hotkeys, normalize_hotkey
from shared.ui_kit import (
    apply_app_theme, Tooltip, make_panel, make_scroll_canvas,
    BG_BASE, BG_ELEVATED, BG_SURFACE, BG_CARD, BG_HOVER, BORDER_SUBTLE,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_YELLOW,
    ACCENT_RED, ACCENT_CYAN, ACCENT_ORANGE,
    FONT_FAMILY,
)
from features.camera_builder.widget import CameraBuilder
from features.ai_optimize.widget   import AIOptimizeDialog
from features.ai_settings.widget   import AISettingsDialog
from features.screenshot_prompt.widget import (
    ScreenshotSelector,
    call_reverse_prompt,
    format_reverse_prompt_result,
    pixmap_to_png_bytes,
    screenshot_analysis_label,
    screenshot_detail_label,
    screenshot_prompt_title,
)
from features.screenshot_settings.widget import ScreenshotSettingsDialog


class PromptTool(tk.Tk):

    def __init__(self):
        super().__init__()
        apply_app_theme()
        self.title("Prompt Studio")
        self.geometry("1120x740")
        self.minsize(980, 640)
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
        self._screenshot_selector = None
        self._screenshot_shortcut = None
        self._prompt_shortcuts = []
        self._hotkey_unavailable: list[str] = []
        self._status_flash_id = 0

        self._build_ui()
        self._bind_shortcuts()
        self._sync_prompts()
        self._refresh_buttons()

    # ─────────────────────────────────────────────────────────────
    #  UI 骨架
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        shell = tk.Frame(self, bg=BG_BASE)
        shell.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        toolbar = make_panel(shell, bg=BG_ELEVATED, padx=14, pady=9)
        toolbar.pack(fill=tk.X)
        brand = tk.Frame(toolbar, bg=BG_ELEVATED)
        brand.pack(side=tk.LEFT)
        title_row = tk.Frame(brand, bg=BG_ELEVATED)
        title_row.pack(anchor="w")
        tk.Label(title_row, text="Prompt Studio", bg=BG_ELEVATED, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 12, "bold")).pack(side=tk.LEFT)
        tk.Label(brand, text="本地提示词工作台 · 生成、优化、收藏", bg=BG_ELEVATED, fg=FG_DIM,
                 font=(FONT_FAMILY, 8)).pack(anchor="w", pady=(1, 0))

        primary_actions = tk.Frame(toolbar, bg=BG_ELEVATED)
        primary_actions.pack(side=tk.LEFT, padx=(34, 0), anchor="center")
        builder_btn = self._primary_btn(primary_actions, "提示词生成器", self._open_camera_builder, width=104)
        builder_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.action_buttons["builder"] = builder_btn
        Tooltip(builder_btn, "提示词生成器\n打开四步式提示词生成器：场景、风格、镜头、输出。")
        shot_group = tk.Frame(primary_actions, bg=BG_ELEVATED)
        shot_group.pack(side=tk.LEFT, padx=(0, 8))
        shot_btn = self._primary_btn(shot_group, "截图", self._start_screenshot_reverse, width=86)
        shot_btn.pack(side=tk.LEFT)
        if shot_group.layout() is not None:
            shot_group.layout().setSpacing(0)
        Tooltip(shot_btn, "截图反推\n框选任意屏幕窗口区域后，由 AI 反推生成提示词并加入列表。")
        shot_settings_btn = self._primary_dropdown_btn(shot_group, self._screenshot_settings)
        shot_settings_btn.pack(side=tk.LEFT, padx=(0, 0))
        Tooltip(shot_settings_btn, "截图分析设置\n选择反推用途、精简/完整长度和自定义要求。")
        optimize_btn = self._primary_btn(primary_actions, "AI 优化", self._ai_optimize, width=100)
        optimize_btn.pack(side=tk.LEFT)
        self.action_buttons["ai_optimize"] = optimize_btn
        Tooltip(optimize_btn, "AI 优化\n对当前选中的 Prompt 做优化、翻译、扩写、评分和合规修复。")

        utility_actions = tk.Frame(toolbar, bg=BG_ELEVATED)
        utility_actions.pack(side=tk.RIGHT, padx=(0, 0), anchor="center")
        settings_btn = self._toolbar_square_btn(utility_actions, "设置", self._ai_settings)
        settings_btn.pack(side=tk.LEFT, padx=(0, 6))
        settings_btn.setFixedSize(48, 48)
        Tooltip(settings_btn, "设置\n配置 AI 服务的 API Key、模型和接口地址。")
        help_btn = self._toolbar_square_btn(utility_actions, "帮助", self._open_help)
        help_btn.pack(side=tk.LEFT, padx=(0, 6))
        help_btn.setFixedSize(48, 48)
        Tooltip(help_btn, "帮助\n查看完整使用说明和功能介绍。")
        self.compact_btn = self._toolbar_square_btn(utility_actions, "精简", self._toggle_compact_mode)
        self.compact_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.compact_btn.setFixedSize(48, 48)
        Tooltip(self.compact_btn, "精简模式\n收起主窗口，弹出一个迷你浮动列表，可拖动放置在屏幕任意位置，便于随时复制 Prompt。")
        self.topmost_btn = self._toolbar_square_btn(utility_actions, "置顶", self._toggle_topmost)
        self.topmost_btn.pack(side=tk.LEFT)
        self.topmost_btn.setFixedSize(48, 48)
        Tooltip(self.topmost_btn, "置顶\n让窗口始终显示在所有其他窗口上方，方便对照使用。")

        workbench = tk.Frame(shell, bg=BG_BASE)
        workbench.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        workbench.grid_columnconfigure(0, weight=2, minsize=300)
        workbench.grid_columnconfigure(1, weight=5, minsize=560)
        workbench.grid_rowconfigure(0, weight=1)

        self.left_pane  = make_panel(workbench, bg=BG_ELEVATED, padx=12, pady=12)
        self.right_pane = make_panel(workbench, bg=BG_SURFACE, padx=12, pady=12)
        self.left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.right_pane.grid(row=0, column=1, sticky="nsew")

        self._build_left_pane()
        self._build_right_pane()

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

        self._canvas, self.btn_frame = make_scroll_canvas(list_frame, bg=BG_ELEVATED)

        # Compact action bar keeps secondary list actions available without heavy boxes.
        action_frame = self._compact_action_bar(self.left_pane)

        primary_row = tk.Frame(action_frame, bg=BG_ELEVATED)
        primary_row.pack(fill=tk.X, pady=(0, 5))
        b_new = self._btn(primary_row, "+ 新建",  self._new_prompt,    ACCENT_GREEN )
        b_new.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_new, "+ 新建\n创建一个新的空白 Prompt 条目，自动进入编辑模式。")
        b_edit = self._btn(primary_row, "编辑",  self._edit_prompt,   ACCENT_BLUE  )
        b_edit.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["edit"] = b_edit
        Tooltip(b_edit, "✎ 编辑\n选中一条 Prompt 后点击，进入编辑模式，可修改标题和内容。编辑完成后点[保存]。")
        b_del = self._btn(primary_row, "删除",  self._delete_prompt, ACCENT_RED   )
        b_del.pack(side=tk.LEFT)
        self.action_buttons["delete"] = b_del
        Tooltip(b_del, "✕ 删除\n删除当前选中的 Prompt（不可撤销，会弹出确认对话框）。")

        utility_row = tk.Frame(action_frame, bg=BG_ELEVATED)
        utility_row.pack(fill=tk.X)
        b_up = self._btn(utility_row, "↑", lambda: self._move(-1), ACCENT_ORANGE)
        b_up.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["move_up"] = b_up
        Tooltip(b_up, "↑ 上移\n将当前选中的 Prompt 在列表中向上移动一位，调整排列顺序。")
        b_dn = self._btn(utility_row, "↓", lambda: self._move(1),  ACCENT_ORANGE)
        b_dn.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["move_down"] = b_dn
        Tooltip(b_dn, "↓ 下移\n将当前选中的 Prompt 在列表中向下移动一位，调整排列顺序。")
        b_copy_checked = self._btn(utility_row, "拼接", self._copy_checked_prompts,  ACCENT_CYAN  )
        b_copy_checked.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["copy_checked"] = b_copy_checked
        Tooltip(b_copy_checked, "☑ 拼接复制\n将所有勾选的 Prompt 内容拼接（用空行分隔），一次性复制到剪贴板，适合组合使用多个 Prompt。")
        b_selall = self._btn(utility_row, "全选",        self._select_all_prompts,    ACCENT_BLUE    )
        b_selall.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_selall, "全选\n勾选列表中的所有 Prompt。")
        b_clrsel = self._btn(utility_row, "清空",    self._clear_checked_prompts, FG_MUTED    )
        b_clrsel.pack(side=tk.LEFT)
        Tooltip(b_clrsel, "清空选择\n取消所有 Prompt 的勾选状态。")

    def _build_right_pane(self):
        header = tk.Frame(self.right_pane, bg=BG_SURFACE)
        header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(header, text="Canvas", bg=BG_SURFACE, fg=FG_DIM,
                 font=(FONT_FAMILY, 8, "bold")).pack(side=tk.RIGHT)
        self.edit_mode_label = tk.Label(header, text="当前提示词", bg=BG_SURFACE, fg=FG_PRIMARY,
                                        font=(FONT_FAMILY, 11, "bold"))
        self.edit_mode_label.pack(side=tk.LEFT)

        title_frame = tk.Frame(self.right_pane, bg=BG_CARD, padx=8, pady=7,
                               highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        title_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(title_frame, text="Title", bg=BG_CARD, fg=FG_DIM,
                 font=(FONT_FAMILY, 8, "bold")).pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(title_frame, textvariable=self.title_var,
                                    bg=BG_CARD, fg=FG_PRIMARY,
                                    insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                    font=(FONT_FAMILY, 10), state=tk.DISABLED,
                                    disabledbackground=BG_SURFACE, disabledforeground=FG_DIM)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(8, 0))

        shortcut_frame = tk.Frame(self.right_pane, bg=BG_SURFACE)
        shortcut_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(shortcut_frame, text="Shortcut", bg=BG_SURFACE, fg=FG_DIM,
                 font=(FONT_FAMILY, 8, "bold")).pack(side=tk.LEFT)
        self.shortcut_var = tk.StringVar()
        self.shortcut_entry = tk.Entry(shortcut_frame, textvariable=self.shortcut_var,
                                       bg=BG_CARD, fg=FG_PRIMARY,
                                       insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                       font=(FONT_FAMILY, 9), state=tk.DISABLED,
                                       disabledbackground=BG_SURFACE, disabledforeground=FG_DIM)
        self.shortcut_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(8, 6))
        self.shortcut_combo = ttk.Combobox(
            shortcut_frame,
            textvariable=self.shortcut_var,
            values=("Ctrl+Alt+1", "Ctrl+Alt+2", "Ctrl+Alt+3", "Ctrl+Shift+1", "Ctrl+Shift+2", "F8", "F9"),
            width=14,
            font=(FONT_FAMILY, 9),
            state=tk.DISABLED,
        )
        self.shortcut_combo.pack(side=tk.LEFT, ipady=4)
        Tooltip(self.shortcut_entry, "Prompt 全局快捷键\n保存后，即使本程序窗口不在前台，按该快捷键也会直接复制此 Prompt 到剪贴板。")

        meta_row = tk.Frame(self.right_pane, bg=BG_SURFACE)
        meta_row.pack(fill=tk.X, pady=(0, 8))
        for text, color in (
            ("本地", ACCENT_GREEN),
            ("可编辑", ACCENT_BLUE),
            ("离线保存", FG_DIM),
        ):
            self._status_pill(meta_row, text, color).pack(side=tk.LEFT, padx=(0, 6))

        self.text_area = tk.Text(self.right_pane, bg=BG_SURFACE, fg=FG_MUTED,
                                 insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                 font=(FONT_FAMILY, 10), wrap=tk.WORD, padx=12, pady=12,
                                 highlightbackground=BORDER_SUBTLE, highlightthickness=1,
                                 state=tk.DISABLED)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        right_bottom = tk.Frame(self.right_pane, bg=BG_SURFACE)
        right_bottom.pack(fill=tk.X, pady=(8, 0))
        b_save = self._btn(right_bottom, "保存",          self._save_edit,     ACCENT_GREEN )
        b_save.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["save"] = b_save
        Tooltip(b_save, "💾 保存\n将编辑区的标题和内容保存到本地文件中（JSON 格式，重启后仍保留）。")
        b_copy = self._btn(right_bottom, "复制",  self._copy_current,  ACCENT_CYAN  )
        b_copy.pack(side=tk.LEFT, padx=(0, 4))
        self.action_buttons["copy_current"] = b_copy
        Tooltip(b_copy, "复制到剪切板\n将右侧编辑区中的 Prompt 内容复制到剪贴板，可直接粘贴到 AI 生图工具中使用。")

        self.status_label = tk.Label(right_bottom, text="", bg=BG_SURFACE,
                                     fg=ACCENT_GREEN, font=(FONT_FAMILY, 9))
        self.status_label.pack(side=tk.LEFT, padx=10)

    def _build_tools_pane(self):
        tk.Label(self.tools_pane, text="Inspector", bg=BG_ELEVATED, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(self.tools_pane, text="常用操作", bg=BG_ELEVATED, fg=ACCENT_BLUE,
                 font=(FONT_FAMILY, 8, "bold")).pack(anchor="w", pady=(0, 6))

        intro = tk.Label(
            self.tools_pane,
            text="主要入口固定在这里：先生成提示词，再对选中的内容做 AI 优化。",
            bg=BG_ELEVATED,
            fg=FG_MUTED,
            font=(FONT_FAMILY, 8),
            justify=tk.LEFT,
            wraplength=220,
        )
        intro.pack(anchor="w", fill=tk.X, pady=(0, 10))

        self._inspector_section("主要")
        self._inspector_action_card(
            "提示词生成器",
            "场景、风格、镜头、输出四步生成",
            self._open_camera_builder,
            ACCENT_GREEN,
            key="builder",
        )
        self._inspector_action_card(
            "AI 优化",
            "优化、翻译、扩写、评分和合规修复",
            self._ai_optimize,
            ACCENT_PURPLE,
            key="ai_optimize",
        )

        self._inspector_section("辅助")
        self._inspector_action_card(
            "AI 设置",
            "服务商、API Key 和模型",
            self._ai_settings,
            ACCENT_BLUE,
        )
        self._inspector_action_card(
            "使用帮助",
            "查看说明和常用操作",
            self._open_help,
            FG_MUTED,
        )

    # ─────────────────────────────────────────────────────────────
    #  工具函数
    # ─────────────────────────────────────────────────────────────
    def _bind_shortcuts(self):
        if self._screenshot_shortcut is not None:
            global_hotkeys.unregister(self._screenshot_shortcut)
            self._screenshot_shortcut = None
        self._hotkey_unavailable = []
        self._screenshot_shortcut = global_hotkeys.register(
            cfg.SCREENSHOT_SHORTCUT,
            self._start_screenshot_reverse,
        )
        self._bind_prompt_shortcuts()
        if self._hotkey_unavailable:
            self._flash_status(f"部分全局快捷键注册失败：{', '.join(self._hotkey_unavailable)}", duration=5000)
        else:
            self._flash_status(f"全局截图快捷键：{cfg.SCREENSHOT_SHORTCUT}")

    def _bind_prompt_shortcuts(self):
        for hotkey_id in self._prompt_shortcuts:
            global_hotkeys.unregister(hotkey_id)
        self._prompt_shortcuts = []
        self._hotkey_unavailable = []
        if self._screenshot_shortcut is None and normalize_prompt_shortcut(cfg.SCREENSHOT_SHORTCUT):
            self._hotkey_unavailable.append(cfg.SCREENSHOT_SHORTCUT)
        used = {normalize_prompt_shortcut(cfg.SCREENSHOT_SHORTCUT)}
        for index, prompt in enumerate(self.prompts):
            sequence = normalize_prompt_shortcut(prompt.shortcut)
            if not sequence or sequence in used:
                continue
            used.add(sequence)
            hotkey_id = global_hotkeys.register(
                sequence,
                lambda idx=index: self._copy_prompt_by_shortcut(idx),
            )
            if hotkey_id is None:
                self._hotkey_unavailable.append(sequence)
                continue
            self._prompt_shortcuts.append(hotkey_id)

    def _compact_action_bar(self, parent):
        toolbar = tk.Frame(parent, bg=BG_ELEVATED)
        toolbar.pack(fill=tk.X, pady=(8, 0))
        tk.Frame(toolbar, bg=BORDER_SUBTLE, height=1).pack(fill=tk.X, pady=(0, 8))
        label = tk.Label(toolbar, text="列表操作", bg=BG_ELEVATED, fg=FG_DIM,
                         font=(FONT_FAMILY, 7, "bold"))
        label.pack(anchor="w", pady=(0, 5))
        return toolbar

    def _status_pill(self, parent, text, color):
        pill = tk.Label(parent, text=text, bg=BG_CARD, fg=color,
                        font=(FONT_FAMILY, 7, "bold"), padx=8, pady=2,
                        highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        return pill

    def _inspector_section(self, title):
        tk.Frame(self.tools_pane, bg=BORDER_SUBTLE, height=1).pack(fill=tk.X, pady=(8, 6))
        tk.Label(self.tools_pane, text=title, bg=BG_ELEVATED, fg=FG_DIM,
                 font=(FONT_FAMILY, 7, "bold")).pack(anchor="w", pady=(0, 6))

    def _inspector_action_card(self, title, desc, command, color, key=None):
        text = f"{title}\n{desc}"
        btn = tk.Button(
            self.tools_pane,
            text=text,
            command=command,
            anchor="w",
            justify=tk.LEFT,
            bg=BG_SURFACE,
            fg=FG_PRIMARY,
            relief=tk.FLAT,
            font=(FONT_FAMILY, 9, "bold"),
            padx=14,
            pady=10,
            cursor="hand2",
            activebackground=BG_HOVER,
            activeforeground=FG_PRIMARY,
            highlightbackground=color,
            highlightthickness=1,
        )
        btn.pack(fill=tk.X, pady=(0, 7))
        if key:
            self.action_buttons[key] = btn
        return btn

    def _btn(self, parent, text, cmd, color=ACCENT_BLUE):
        return tk.Button(parent, text=text, command=cmd,
                         bg=BG_CARD, fg=color, relief=tk.FLAT,
                         font=(FONT_FAMILY, 9, "bold"), padx=10, pady=4,
                         activebackground=BG_HOVER, cursor="hand2",
                         highlightbackground=color, highlightthickness=1)

    def _primary_btn(self, parent, text, cmd, width=118):
        btn = tk.Button(parent, text=text, command=cmd,
                        bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
                        font=(FONT_FAMILY, 9, "bold"), padx=0, pady=0,
                        activebackground=BG_HOVER, cursor="hand2",
                        highlightbackground=ACCENT_BLUE, highlightthickness=1)
        btn._is_primary_action = True
        btn.setMinimumSize(width, 32)
        btn.setMaximumSize(width, 32)
        btn._apply_style()
        return btn

    def _primary_dropdown_btn(self, parent, cmd):
        btn = tk.Button(parent, text="▼", command=cmd,
                        bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
                        font=(FONT_FAMILY, 10, "bold"), padx=0, pady=0,
                        activebackground=BG_HOVER, cursor="hand2",
                        highlightbackground=ACCENT_BLUE, highlightthickness=1)
        btn._is_primary_dropdown = True
        btn.setMinimumSize(30, 32)
        btn.setMaximumSize(30, 32)
        btn._apply_style()
        return btn

    def _toolbar_square_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, command=cmd,
                        bg=BG_CARD, fg=FG_PRIMARY, relief=tk.FLAT,
                        font=(FONT_FAMILY, 9, "bold"), padx=0, pady=0,
                        activebackground=BG_HOVER, cursor="hand2",
                        highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        btn._is_toolbar_square = True
        btn._apply_style()
        btn.setFixedSize(48, 48)
        return btn

    def _flash_status(self, msg, duration=2000):
        self._status_flash_id += 1
        flash_id = self._status_flash_id
        self.status_label.config(text=msg)
        self.after(duration, lambda: self.status_label.config(text="") if flash_id == self._status_flash_id else None)

    def _sync_prompts(self):
        self.prompts = self.prompt_service.prompts
        self.checked_indices = self.prompt_service.checked_indices
        self._refresh_library_status()
        self._refresh_empty_state()
        self._refresh_action_states()
        self._bind_prompt_shortcuts()

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
            # Top-level workflow entry should remain clickable after startup;
            # _ai_optimize gives a clear prompt if no usable content is selected.
            "ai_optimize": True,
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
            "还没有提示词。\n\n新建提示词：点击左下「+ 新建」。\n"
            "打开生成器：使用顶部「提示词生成器」快速生成。"
            if not self.prompts else
            "选择左侧提示词查看内容。\n\n也可以新建提示词，或使用顶部入口打开生成器。"
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
        self.shortcut_entry.config(state=state)
        self.shortcut_combo.config(state=state)
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

            selected = i == self.selected_index
            row_bg = "#223047" if selected else BG_ELEVATED
            row = tk.Frame(self.btn_frame, bg=row_bg)
            row.setMinimumHeight(42)
            row.setMaximumHeight(42)
            row.config(cursor="hand2")
            row.config(highlightthickness=0)
            row.bind("<Button-1>", lambda _e, idx=i: self._select(idx))
            row.pack(fill=tk.X, pady=2)
            strip = tk.Frame(row, bg=ACCENT_BLUE if selected else row_bg)
            strip.setFixedWidth(4)
            strip.setStyleSheet(
                f"background-color: {ACCENT_BLUE if selected else row_bg}; "
                "border: none; border-radius: 0px;"
            )
            strip.config(cursor="hand2")
            strip.bind("<Button-1>", lambda _e, idx=i: self._select(idx))
            strip.pack(side=tk.LEFT, fill=tk.Y)

            checked = tk.BooleanVar(value=i in self.checked_indices)
            self.check_vars[i] = checked
            tk.Checkbutton(row, variable=checked,
                           bg=row.cget("bg"), activebackground=row.cget("bg"),
                           selectcolor=BG_CARD, fg=FG_PRIMARY,
                           relief=tk.FLAT, highlightthickness=0, bd=0,
                           command=lambda _checked=False, idx=i: self._toggle_check(idx)
                           ).pack(side=tk.LEFT, padx=(6, 4))

            label = p.display_label()
            btn = tk.Button(row, text=label, anchor="w",
                            bg=row.cget("bg"), fg=FG_PRIMARY if not selected else "#ffffff", relief=tk.FLAT,
                            font=(FONT_FAMILY, 9), padx=8, pady=6,
                            activebackground=BG_HOVER, cursor="hand2",
                            highlightthickness=0,
                            command=lambda _checked=False, idx=i: self._select(idx))
            btn.setMinimumHeight(38)
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
    def _select(self, index, flash_copy=True):
        self.selected_index = index
        self._sync_prompts()
        p = self.prompts[index]
        self._set_edit_mode(False)
        self.title_var.set(p.title)
        self.shortcut_var.set(p.shortcut)
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", p.content)
        self.text_area.config(state=tk.DISABLED)
        pyperclip.copy(p.content)
        if flash_copy:
            self._flash_status("已复制到剪切板 ✓")
        self._refresh_buttons()

    def _new_prompt(self):
        idx = self.prompt_service.add_prompt(title="新 Prompt", content="")
        self.selected_index = idx
        self._sync_prompts()
        self._set_edit_mode(True)
        self.title_var.set("新 Prompt")
        self.shortcut_var.set("")
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
        shortcut = normalize_prompt_shortcut(self.shortcut_var.get())
        if self.shortcut_var.get().strip() and not shortcut:
            messagebox.showinfo("提示", "快捷键无效，请输入例如 Ctrl+Alt+1 或 F8 的格式。", parent=self)
            return
        if shortcut and self._shortcut_conflicts(shortcut, self.selected_index):
            messagebox.showinfo("提示", f"快捷键 {shortcut} 已被使用，请换一个。", parent=self)
            return
        self.shortcut_var.set(shortcut)
        self.prompt_service.update_prompt(self.selected_index, title, content, shortcut)
        self._sync_prompts()
        self._set_edit_mode(False)
        self._refresh_buttons()
        self._flash_status("已保存 ✓")

    def _delete_prompt(self):
        if self.selected_index is None:
            messagebox.showinfo("提示", "请先选择一个 Prompt")
            return
        title = self.prompts[self.selected_index].title
        if not messagebox.askyesno("确认删除", f"确定要删除「{title}」吗？此操作不可撤销。", parent=self):
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
            self.shortcut_var.set("")
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

    def _copy_prompt_by_shortcut(self, index):
        if not 0 <= index < len(self.prompts):
            return
        prompt = self.prompts[index]
        if not prompt.content:
            self._flash_status(f"「{prompt.display_label()}」内容为空")
            return
        pyperclip.copy(prompt.content)
        self._flash_status(f"快捷键已复制「{prompt.display_label()}」✓")

    def _shortcut_conflicts(self, shortcut: str, current_index: int) -> bool:
        if shortcut == normalize_prompt_shortcut(cfg.SCREENSHOT_SHORTCUT):
            return True
        return any(
            i != current_index and normalize_prompt_shortcut(prompt.shortcut) == shortcut
            for i, prompt in enumerate(self.prompts)
        )

    def _context_menu(self, event, index):
        menu = tk.Menu(self, tearoff=0, bg=BG_CARD, fg=FG_PRIMARY,
                       activebackground=BG_HOVER, relief=tk.FLAT)
        menu.add_command(label="复制内容",
                         command=lambda _checked=False: self._select(index))
        menu.add_command(label="编辑",
                         command=lambda _checked=False: (self._select(index), self._edit_prompt()))
        menu.add_separator()
        menu.add_command(label="删除",
                         command=lambda _checked=False: (
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
            self.compact_btn.config(text="精简")

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
        ov.geometry(f"280x560+{bx}+{by + bh + 4}")
        self._compact_win = ov

        ov._drag_x = ov._drag_y = 0
        def _on_press(e):
            ov._drag_x = e.x_root - ov.winfo_x()
            ov._drag_y = e.y_root - ov.winfo_y()
        def _on_drag(e):
            ov.geometry(f"+{e.x_root - ov._drag_x}+{e.y_root - ov._drag_y}")

        bar = tk.Frame(ov, bg=BG_CARD, height=24)
        bar.pack(fill=tk.X)
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_columnconfigure(1, weight=0)
        bar.bind("<Button-1>", _on_press)
        bar.bind("<B1-Motion>", _on_drag)
        lbl = tk.Label(bar, text="Prompts  ·  拖动移动", bg=BG_CARD, fg=FG_MUTED,
                       font=(FONT_FAMILY, 8))
        lbl.grid(row=0, column=0, sticky="w", padx=(8, 4), pady=2)
        lbl.bind("<Button-1>", _on_press)
        lbl.bind("<B1-Motion>", _on_drag)
        restore_btn = tk.Button(bar, text="恢复", command=self._exit_compact,
                                bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
                                font=(FONT_FAMILY, 8, "bold"), padx=0, pady=0,
                                cursor="hand2", activebackground=BG_HOVER,
                                highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        restore_btn._is_compact_restore = True
        restore_btn.setFixedSize(52, 24)
        restore_btn._apply_style()
        restore_btn.grid(row=0, column=1, sticky="e", padx=(0, 6), pady=3)

        list_frame = tk.Frame(ov, bg=BG_BASE)
        list_frame.pack(fill=tk.BOTH, expand=True)
        canvas, inner = make_scroll_canvas(list_frame, bg=BG_BASE)
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
                      font=(FONT_FAMILY, 9), padx=8, pady=5,
                      activebackground=BG_HOVER, cursor="hand2",
                      command=lambda _checked=False, idx=i: self._compact_select(idx)
                      ).pack(fill=tk.X, pady=1, padx=2)

    def _compact_select(self, index):
        self._select(index)
        self._refresh_compact_list()

    def _exit_compact(self):
        self.compact_mode = False
        if hasattr(self, "_compact_win") and self._compact_win.winfo_exists():
            self._compact_win.destroy()
        self.deiconify()
        self.compact_btn.config(text="精简")

    def _toggle_topmost(self):
        self.topmost_mode = not self.topmost_mode
        self.attributes("-topmost", self.topmost_mode)
        self.topmost_btn.config(
            text="取消" if self.topmost_mode else "置顶")

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
        AISettingsDialog(self, on_save=self._bind_shortcuts)

    def _screenshot_settings(self):
        ScreenshotSettingsDialog(self, on_save=lambda: self._flash_status(
            f"截图分析计划已保存：{screenshot_analysis_label()} / {screenshot_detail_label()}",
            duration=3000,
        ))

    def _open_help(self):
        from features.help.widget import HelpDialog
        HelpDialog(self)

    def _start_screenshot_reverse(self):
        self._flash_status(f"准备截图：{screenshot_analysis_label()} / {screenshot_detail_label()}，Esc / 右键取消")
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
            self.update_idletasks()

        def _begin_selector():
            self._screenshot_selector = ScreenshotSelector(
                on_selected=lambda pixmap: self._finish_screenshot_selection(pixmap, was_visible),
                on_cancel=lambda: self._cancel_screenshot_selection(was_visible),
            )

        self.after(180, _begin_selector)

    def _finish_screenshot_selection(self, pixmap, restore_main: bool):
        if restore_main:
            self.show()
            self.raise_()
            self.activateWindow()
        self._reverse_prompt_from_pixmap(pixmap)

    def _cancel_screenshot_selection(self, restore_main: bool):
        if restore_main:
            self.show()
            self.raise_()
            self.activateWindow()
        self._flash_status("已取消截图反推")

    def _reverse_prompt_from_pixmap(self, pixmap):
        png_bytes = pixmap_to_png_bytes(pixmap)
        if not png_bytes:
            messagebox.showinfo("提示", "截图失败，请重新框选。")
            return
        mode_label = screenshot_analysis_label()
        self._flash_status(f"正在按「{mode_label}」反推截图 Prompt...")

        def _on_ok(text):
            def _show():
                title = screenshot_prompt_title()
                content = format_reverse_prompt_result(text)
                idx = self.prompt_service.add_prompt(title=title, content=content)
                self._show_all_prompts_after_generated()
                self._sync_prompts()
                self._select(idx, flash_copy=False)
                self._flash_status(
                    f"截图反推完成：已创建「{title}」，右侧已显示，内容已复制 ✓",
                    duration=8000,
                )
            self.after(0, _show)

        def _on_model(model, note):
            suffix = f"（{note}）" if note else ""
            self.after(0, lambda: self._flash_status(f"正在按「{mode_label}」反推截图 Prompt... 模型：{model}{suffix}", duration=30000))

        def _on_err(msg):
            def _show():
                self._flash_status("截图反推失败")
                messagebox.showinfo(
                    "截图反推失败",
                    f"{msg}\n\n请在 AI 设置中单独配置“截图服务 / 截图模型”，文字优化模型可以继续使用不支持图片的模型。",
                    parent=self,
                )
            self.after(0, _show)

        call_reverse_prompt(png_bytes, _on_ok, _on_err, on_model=_on_model)

    def _show_all_prompts_after_generated(self):
        if not hasattr(self, "_search_entry") or self._search_entry.get() == "Search":
            return
        self._search_entry.delete(0, tk.END)
        self._search_entry.insert(0, "Search")
        self._search_entry.config(fg=FG_DIM)

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
            title = simpledialog.askstring(
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

    def destroy(self):
        if self._screenshot_shortcut is not None:
            global_hotkeys.unregister(self._screenshot_shortcut)
            self._screenshot_shortcut = None
        for hotkey_id in list(self._prompt_shortcuts):
            global_hotkeys.unregister(hotkey_id)
        self._prompt_shortcuts = []
        super().destroy()


def normalize_prompt_shortcut(sequence: str) -> str:
    return normalize_hotkey(sequence)
