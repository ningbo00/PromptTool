"""
主窗口 PromptTool：Prompt 列表管理 + 编辑区 + 工具栏
"""
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.simpledialog
import pyperclip

from core.domain.prompt_library import PromptLibrary, PromptSelection
from shared.storage import load_prompts, save_prompts
from shared.ui_kit import (
    bind_mousewheel, Tooltip,
    BG_BASE, BG_SURFACE, BG_CARD, BG_HOVER,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_YELLOW,
    ACCENT_RED, ACCENT_CYAN, ACCENT_ORANGE, DARK_TEXT,
)
from features.camera_builder.widget import CameraBuilder
from features.ai_optimize.widget   import AIOptimizeDialog
from features.ai_settings.widget   import AISettingsDialog


class PromptTool(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Prompt 管理工具")
        self.geometry("1100x720")
        self.configure(bg=BG_BASE)
        self.resizable(True, True)

        self.library         = PromptLibrary(load_prompts())
        self.prompts         = self.library.prompts
        self.selected_index  = None
        self.selection       = PromptSelection()
        self.checked_indices = self.selection.checked_indices
        self.check_vars      = {}
        self.compact_mode    = False
        self.topmost_mode    = False

        self._build_ui()
        self._refresh_buttons()

    # ─────────────────────────────────────────────────────────────
    #  UI 骨架
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        toolbar = tk.Frame(self, bg="#181825")
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 0))
        tk.Label(toolbar, text="Prompt 管理工具", bg="#181825", fg=FG_PRIMARY,
                 font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)

        self.topmost_btn = self._btn(toolbar, "📌 置顶",     self._toggle_topmost,      ACCENT_YELLOW)
        self.topmost_btn.pack(side=tk.RIGHT, padx=(6, 0))
        Tooltip(self.topmost_btn, "📌 置顶\n让窗口始终显示在所有其他窗口上方，方便对照使用。")
        self.compact_btn = self._btn(toolbar, "🗂 精简模式", self._toggle_compact_mode, "#94e2d5")
        self.compact_btn.pack(side=tk.RIGHT)
        Tooltip(self.compact_btn, "🗂 精简模式\n收起主窗口，弹出一个迷你浮动列表，可拖动放置在屏幕任意位置，便于随时复制 Prompt。")
        help_btn = self._btn(toolbar, "❓ 帮助", self._open_help, BG_HOVER)
        help_btn.config(fg=FG_PRIMARY)
        help_btn.pack(side=tk.RIGHT, padx=(0, 6))
        Tooltip(help_btn, "❓ 帮助\n查看完整使用说明和功能介绍。")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Main.Horizontal.TPanedwindow", background=BG_BASE)

        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL,
                                     style="Main.Horizontal.TPanedwindow")
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_pane  = tk.Frame(self.paned, bg=BG_BASE)
        self.right_pane = tk.Frame(self.paned, bg="#181825")
        self.paned.add(self.left_pane,  weight=1)
        self.paned.add(self.right_pane, weight=3)

        self._build_left_pane()
        self._build_right_pane()

    def _build_left_pane(self):
        tk.Label(self.left_pane, text="Prompt 列表", bg=BG_BASE, fg=FG_PRIMARY,
                 font=("微软雅黑", 11, "bold")).pack(anchor="w", pady=(0, 6))

        # 搜索框
        self.search_var = tk.StringVar()
        self._search_entry = tk.Entry(self.left_pane, textvariable=self.search_var,
                                      bg=BG_CARD, fg=FG_DIM,
                                      insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                      font=("微软雅黑", 9))
        self._search_entry.pack(fill=tk.X, ipady=5, pady=(0, 8))
        self._search_entry.insert(0, "搜索...")
        self.search_var.trace_add("write", lambda *_: self._refresh_buttons())
        self._search_entry.bind("<FocusIn>",  self._search_focus_in)
        self._search_entry.bind("<FocusOut>", self._search_focus_out)

        # 列表区（带滚动）
        list_frame = tk.Frame(self.left_pane, bg=BG_BASE)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(list_frame, bg=BG_BASE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self._canvas.yview)
        self.btn_frame = tk.Frame(self._canvas, bg=BG_BASE)
        self.btn_frame.bind("<Configure>",
                            lambda _e: self._canvas.configure(
                                scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self.btn_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        bind_mousewheel(self._canvas)

        # 操作按钮组
        action_frame = tk.Frame(self.left_pane, bg=BG_BASE)
        action_frame.pack(fill=tk.X, pady=(8, 0))

        def _row():
            r = tk.Frame(action_frame, bg=BG_BASE)
            r.pack(fill=tk.X, pady=(0, 4))
            return r

        r1 = _row()
        b_new = self._btn(r1, "+ 新建",  self._new_prompt,    ACCENT_GREEN )
        b_new.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_new, "+ 新建\n创建一个新的空白 Prompt 条目，自动进入编辑模式。")
        b_edit = self._btn(r1, "✎ 编辑",  self._edit_prompt,   ACCENT_BLUE  )
        b_edit.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_edit, "✎ 编辑\n选中一条 Prompt 后点击，进入编辑模式，可修改标题和内容。编辑完成后点[保存]。")
        b_del = self._btn(r1, "✕ 删除",  self._delete_prompt, ACCENT_RED   )
        b_del.pack(side=tk.LEFT)
        Tooltip(b_del, "✕ 删除\n删除当前选中的 Prompt（不可撤销，会弹出确认对话框）。")

        r2 = _row()
        b_up = self._btn(r2, "↑ 上移", lambda: self._move(-1), ACCENT_ORANGE)
        b_up.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_up, "↑ 上移\n将当前选中的 Prompt 在列表中向上移动一位，调整排列顺序。")
        b_dn = self._btn(r2, "↓ 下移", lambda: self._move(1),  ACCENT_ORANGE)
        b_dn.pack(side=tk.LEFT)
        Tooltip(b_dn, "↓ 下移\n将当前选中的 Prompt 在列表中向下移动一位，调整排列顺序。")

        r3 = _row()
        b_copy_checked = self._btn(r3, "☑ 拼接复制", self._copy_checked_prompts,  ACCENT_CYAN  )
        b_copy_checked.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_copy_checked, "☑ 拼接复制\n将所有勾选的 Prompt 内容拼接（用空行分隔），一次性复制到剪贴板，适合组合使用多个 Prompt。")
        b_selall = self._btn(r3, "全选",        self._select_all_prompts,    "#74c7ec"    )
        b_selall.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_selall, "全选\n勾选列表中的所有 Prompt。")
        b_clrsel = self._btn(r3, "清空选择",    self._clear_checked_prompts, "#9399b2"    )
        b_clrsel.pack(side=tk.LEFT)
        Tooltip(b_clrsel, "清空选择\n取消所有 Prompt 的勾选状态。")

        r4 = _row()
        b_cam = self._btn(r4, "✨ 提示词生成器", self._open_camera_builder,
                  ACCENT_PURPLE)
        b_cam.pack(side=tk.LEFT, fill=tk.X, expand=True)
        Tooltip(b_cam, "✨ 提示词生成器\n打开专业摄影参数构建器，通过可视化选项（景别、光线、风格等）自动生成高质量英文 Prompt，并一键插入列表。")

    def _build_right_pane(self):
        header = tk.Frame(self.right_pane, bg="#181825")
        header.pack(fill=tk.X, pady=(0, 6))
        self.edit_mode_label = tk.Label(header, text="预览", bg="#181825", fg=FG_PRIMARY,
                                        font=("微软雅黑", 11, "bold"))
        self.edit_mode_label.pack(side=tk.LEFT)

        title_frame = tk.Frame(self.right_pane, bg="#181825")
        title_frame.pack(fill=tk.X, pady=(0, 6))
        tk.Label(title_frame, text="标题:", bg="#181825", fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(title_frame, textvariable=self.title_var,
                                    bg=BG_CARD, fg=FG_PRIMARY,
                                    insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                    font=("微软雅黑", 10), state=tk.DISABLED,
                                    disabledbackground=BG_SURFACE, disabledforeground=FG_DIM)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(6, 0))

        self.text_area = tk.Text(self.right_pane, bg=BG_SURFACE, fg=FG_MUTED,
                                 insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                 font=("微软雅黑", 10), wrap=tk.WORD, padx=10, pady=10,
                                 state=tk.DISABLED)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        right_bottom = tk.Frame(self.right_pane, bg="#181825")
        right_bottom.pack(fill=tk.X, pady=(8, 0))
        b_save = self._btn(right_bottom, "💾 保存",          self._save_edit,     ACCENT_GREEN )
        b_save.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_save, "💾 保存\n将编辑区的标题和内容保存到本地文件中（JSON 格式，重启后仍保留）。")
        b_copy = self._btn(right_bottom, "📋 复制到剪切板",  self._copy_current,  ACCENT_CYAN  )
        b_copy.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_copy, "📋 复制到剪切板\n将右侧编辑区中的 Prompt 内容复制到剪贴板，可直接粘贴到 AI 生图工具中使用。")
        b_ai = self._btn(right_bottom, "🤖 AI 优化",       self._ai_optimize,   ACCENT_PURPLE)
        b_ai.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(b_ai, "🤖 AI 优化\n打开 AI 协助优化窗口。可以对当前 Prompt 进行语法优化、扩写、中文转英文、生成多个变体等 10 余种 AI 操作。需要先在[AI 设置]中配置 API Key。")
        b_set = self._btn(right_bottom, "⚙ AI 设置",        self._ai_settings,   BG_HOVER     )
        b_set.pack(side=tk.LEFT)
        Tooltip(b_set, "⚙ AI 设置\n配置 AI 服务的 API Key、模型和接口地址。支持 OpenAI 兼容格式的各类 AI 服务（如 DeepSeek、Qwen 等）。")

        self.status_label = tk.Label(right_bottom, text="", bg="#181825",
                                     fg=ACCENT_GREEN, font=("微软雅黑", 9))
        self.status_label.pack(side=tk.LEFT, padx=10)

    # ─────────────────────────────────────────────────────────────
    #  工具函数
    # ─────────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, color=ACCENT_BLUE):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color, fg=DARK_TEXT, relief=tk.FLAT,
                         font=("微软雅黑", 9, "bold"), padx=10, pady=4,
                         activebackground=color, cursor="hand2")

    def _flash_status(self, msg):
        self.status_label.config(text=msg)
        self.after(2000, lambda: self.status_label.config(text=""))

    def _sync_prompts(self):
        self.prompts = self.library.prompts
        self.checked_indices = self.selection.checked_indices

    def _save_library(self):
        save_prompts(self.library.to_dicts())

    def _set_edit_mode(self, editable: bool):
        state = tk.NORMAL if editable else tk.DISABLED
        self.text_area.config(state=state,
                              bg=BG_CARD if editable else BG_SURFACE,
                              fg=FG_PRIMARY if editable else FG_MUTED)
        self.title_entry.config(state=state)
        self.edit_mode_label.config(text="编辑中..." if editable else "预览")

    # ─────────────────────────────────────────────────────────────
    #  搜索栏
    # ─────────────────────────────────────────────────────────────
    def _search_focus_in(self, _e):
        if self._search_entry.get() == "搜索...":
            self._search_entry.delete(0, tk.END)
            self._search_entry.config(fg=FG_PRIMARY)

    def _search_focus_out(self, _e):
        if not self._search_entry.get():
            self._search_entry.insert(0, "搜索...")
            self._search_entry.config(fg=FG_DIM)

    # ─────────────────────────────────────────────────────────────
    #  列表刷新
    # ─────────────────────────────────────────────────────────────
    def _refresh_buttons(self):
        for w in self.btn_frame.winfo_children():
            w.destroy()
        self.check_vars.clear()

        visible_indices = self.library.search(self.search_var.get())

        for i in visible_indices:
            p = self.prompts[i]

            row = tk.Frame(self.btn_frame,
                           bg=BG_HOVER if i == self.selected_index else BG_CARD)
            row.pack(fill=tk.X, pady=2)

            checked = tk.BooleanVar(value=i in self.checked_indices)
            self.check_vars[i] = checked
            tk.Checkbutton(row, variable=checked,
                           bg=row.cget("bg"), activebackground=row.cget("bg"),
                           selectcolor="#585b70", fg=FG_PRIMARY,
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
        self.selection.toggle(index)
        self._sync_prompts()
        if index in self.check_vars:
            self.check_vars[index].set(index in self.checked_indices)

    def _reindex_checked_after_delete(self, deleted_index):
        self.selection.reindex_after_delete(deleted_index)
        self._sync_prompts()

    def _swap_checked_indices(self, i, j):
        self.selection.swap_indices(i, j)
        self._sync_prompts()

    def _copy_checked_prompts(self):
        content = self.selection.join_checked_contents(self.library)
        if not content:
            messagebox.showinfo("提示", "请先勾选至少一个 Prompt")
            return
        pyperclip.copy(content)
        self._flash_status(f"已拼接复制 {len(self.checked_indices)} 条 ✓")

    def _select_all_prompts(self):
        self.selection.select_all(self.library)
        self._sync_prompts()
        self._refresh_buttons()
        self._flash_status("已全选 ✓")

    def _clear_checked_prompts(self):
        self.selection.clear()
        self._sync_prompts()
        self._refresh_buttons()
        self._flash_status("已清空选择 ✓")

    # ─────────────────────────────────────────────────────────────
    #  单条选择 / CRUD
    # ─────────────────────────────────────────────────────────────
    def _select(self, index):
        self.selected_index = index
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
        idx = self.library.add_prompt(title="新 Prompt", content="")
        self._sync_prompts()
        self._save_library()
        self.selected_index = idx
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
        self.library.update_prompt(self.selected_index, title, content)
        self._sync_prompts()
        self._save_library()
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
        self.library.delete_prompt(deleted_index)
        self._sync_prompts()
        self._reindex_checked_after_delete(deleted_index)
        if self.prompts:
            self.selected_index = min(deleted_index, len(self.prompts) - 1)
            self._select(self.selected_index)
        else:
            self.selected_index = None
            self._set_edit_mode(False)
            self.title_var.set("")
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(state=tk.DISABLED)
            self._refresh_buttons()
        self._save_library()
        self._refresh_buttons()

    def _move(self, direction):
        if self.selected_index is None:
            messagebox.showinfo("提示", "请先选择一个 Prompt")
            return
        i = self.selected_index
        j = self.library.move_prompt(i, direction)
        if j == i:
            self._flash_status("已经到边界了")
            return
        self._swap_checked_indices(i, j)
        self.selected_index = j
        self._sync_prompts()
        self._save_library()
        self._refresh_buttons()

    def _copy_current(self):
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
        self.library.add_prompt(title=title, content=content)
        self._sync_prompts()
        self._save_library()
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
            self.library.add_prompt(title=title.strip() or "AI优化结果", content=result)
            self._sync_prompts()
            self._save_library()
            self._refresh_buttons()
            self._flash_status(f"「{title.strip()}」已另存为新 Prompt ✓")

        AIOptimizeDialog(self, current_prompt=current,
                         on_apply=_on_apply, on_saveas=_on_saveas)
