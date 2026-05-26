"""
摄影机参数构建器窗口（从 main.py 抽取，依赖 shared/ 和 presets.py）
"""
import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog

from shared.ui_kit import (
    apply_dark_notebook_style, Tooltip,
    BG_BASE, BG_HOVER,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE,
    ACCENT_RED, ACCENT_CYAN, DARK_TEXT,
)
from core.services.camera_prompt_service import append_negative_as_positive, resolve_preset_values
from features.camera_builder.scene_step import create_scene_step, build_subject_tab, refresh_subject_chips
from features.camera_builder.style_step import (
    create_style_step, build_preset_tab, build_style_tab, build_filter_tab,
    build_extractor_tab, refresh_style_blocks,
)
from features.camera_builder.camera_step import (
    create_camera_step, build_params_tab, build_camera_tab, render_params,
)
from features.camera_builder.output_step import create_output_step, build_detail_tab, refresh_detail_blocks
from features.camera_builder.preview_panel import PreviewPanel
from features.camera_builder.state_collector import CameraBuilderStateCollector
from features.camera_builder.presets import (
    PARAMS_REAL, PARAMS_ANIME,
    SHOT_SCALE, CAMERA_ELEVATION, SUBJECT_ANGLE,
    PRESETS_REAL, PRESETS_ANIME,
)


class CameraBuilder(tk.Toplevel):

    def __init__(self, parent, on_insert):
        super().__init__(parent)
        self.on_insert = on_insert
        self.title("提示词生成器")
        self.geometry("980x780")
        self.minsize(920, 720)
        self.configure(bg=BG_BASE)
        self.resizable(True, True)
        self.grab_set()

        # 状态变量
        self.is_anime         = tk.BooleanVar(value=False)
        self.param_vars       = {}
        self.custom_vars      = {}
        self.param_checks     = {}
        self.filter_toggles   = {}
        self.filter_labels    = {}
        self.filter_custom_vars = {}

        self.shot_var             = tk.IntVar(value=3)
        self.shot_enabled         = tk.BooleanVar(value=True)
        self.elevation_var        = tk.IntVar(value=3)
        self.elevation_enabled    = tk.BooleanVar(value=False)
        self.subject_angle_var    = tk.IntVar(value=0)
        self.subject_angle_enabled = tk.BooleanVar(value=False)

        self.light_azimuth    = tk.DoubleVar(value=45.0)
        self.light_elevation  = tk.DoubleVar(value=30.0)
        self.light_dir_enabled = tk.BooleanVar(value=False)
        self.light_color      = "#ffffff"
        self.light_back_mode  = tk.BooleanVar(value=False)
        self.rim_light_var    = tk.BooleanVar(value=False)

        self.extra_var        = tk.StringVar()

        self.neg_to_positive_enabled = tk.BooleanVar(value=False)
        self._neg_btn_ref = None  # reference to the toggle button
        # 风格提炼器
        self._extractor_presets = []
        self._extractor_selected_idx = None

        # 主体场景 Tab
        self.subject_text     = None
        self.environ_text     = None
        self._subject_chips_frame  = None
        self._environ_chips_frame  = None
        self._count_chips_frame    = None
        self._weather_chips_frame  = None
        # 风格情绪 Tab
        self.style_toggles     = {}
        self.aesthetic_toggles = {}
        self.mood_toggles      = {}
        self.motion_var        = tk.StringVar(value="（不指定）")
        self._style_grid       = None
        self._aesthetic_grid   = None
        self._mood_grid        = None
        # 细节技术 Tab
        self.texture_toggles  = {}
        self.quality_toggles  = {}
        self.color_toggles    = {}
        self.render_var       = tk.StringVar(value="（不指定）")
        self.ratio_var        = tk.StringVar(value="（不指定）")
        self.neg_text         = None
        self._texture_grid    = None
        self._quality_grid    = None
        self._color_grid      = None
        self.neg_preview_text = None   # 右侧预览区负面词显示
        self.neg_zh_preview_text = None  # 右侧预览区负面词中文对照

        # 控件引用
        self.nb                   = None
        self.tab_params           = None
        self.tab_camera           = None
        self.tab_filter           = None
        self.tab_preset           = None
        self._params_scroll_host  = None
        self.preview_text         = None
        self.preview_zh_text      = None
        self._mode_btn            = None
        self.shot_result_label    = None
        self.elevation_result_label = None
        self.angle_result_label   = None
        self._light_sphere_canvas = None
        self._light_dot_id        = None
        self._light_color_btn     = None
        self._light_color_label   = None
        self._azimuth_label       = None
        self._elev_label          = None
        self._light_kw_label      = None
        self._rim_btn             = None
        self._hemi_front_btn      = None
        self._hemi_back_btn       = None
        self.tab_extractor        = None
        self._extractor_list_frame = None
        self._extractor_detail_frame = None
        self._state_collector = CameraBuilderStateCollector(self)

        self._build_ui()
        self._generate()

    # ─────────────────────────────────────────────────────────────
    #  UI 骨架
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_topbar()
        self._build_main_area()

    def _build_topbar(self):
        top = tk.Frame(self, bg=BG_BASE)
        top.pack(fill=tk.X, padx=16, pady=(10, 4))

        tk.Label(top, text="✨ 提示词生成器", bg=BG_BASE, fg=FG_PRIMARY,
                 font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)

        def _rb(text, cmd, color):
            return tk.Button(top, text=text, command=cmd,
                             bg=color, fg=DARK_TEXT, relief=tk.FLAT,
                             font=("微软雅黑", 9, "bold"), padx=10, pady=3,
                             cursor="hand2", activebackground=color)

        b_close = _rb("✕ 关闭",   self.destroy,    ACCENT_RED   )
        b_close.pack(side=tk.RIGHT, padx=(4, 0))
        Tooltip(b_close, "✕ 关闭\n关闭提示词生成器，返回主窗口。")
        b_insert = _rb("➕ 插入列表", self._insert,  ACCENT_GREEN )
        b_insert.pack(side=tk.RIGHT, padx=(4, 0))
        Tooltip(b_insert, "➕ 插入列表\n将当前生成的正面提示词保存为新条目插入主列表（会弹出标题输入框）。")
        b_copy = _rb("📋 复制",  self._copy,       ACCENT_CYAN  )
        b_copy.pack(side=tk.RIGHT, padx=(4, 0))
        Tooltip(b_copy, "📋 复制\n将当前生成的正面提示词复制到剪贴板，可直接粘贴到任意 AI 生图工具。")
        b_gen = _rb("🪄 生成",  self._generate,   ACCENT_BLUE  )
        b_gen.pack(side=tk.RIGHT, padx=(4, 0))
        Tooltip(b_gen, "🪄 生成\n根据当前所有选项重新生成提示词（通常会自动触发，手动点击可强制刷新）。")

        tk.Frame(top, bg=BG_HOVER, width=1).pack(side=tk.RIGHT, fill=tk.Y, padx=8)
        tk.Label(top, text="二次元模式", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.RIGHT)
        self._mode_btn = tk.Button(top, text="○ 关", bg=BG_HOVER, fg=FG_PRIMARY,
                                   relief=tk.FLAT, font=("微软雅黑", 9, "bold"),
                                   padx=10, pady=3, cursor="hand2",
                                   command=self._toggle_mode)
        self._mode_btn.pack(side=tk.RIGHT, padx=(0, 4))
        Tooltip(self._mode_btn, "二次元模式\n切换参数、风格词块等内容在[实拍摄影]和[二次元动画]两套预设之间切换。\n开启后参数、风格词全部替换为动漫专用词汇。")

    def _build_main_area(self):
        style = ttk.Style()
        style.configure("H.TPanedwindow", background=BG_BASE)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL, style="H.TPanedwindow")
        paned.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 12))

        nb_host = tk.Frame(paned, bg=BG_BASE)
        paned.add(nb_host, weight=1)
        self._build_notebook(nb_host)

        right = tk.Frame(paned, bg="#181825")
        paned.add(right, weight=1)
        PreviewPanel.build(self, right)

        self.after(20, lambda p=paned: p.sash_place(0, (self.winfo_width() - 32) // 2, 0))

    def _build_notebook(self, parent):
        apply_dark_notebook_style()
        self.nb = ttk.Notebook(parent, style="Dark.TNotebook")
        self.nb.pack(fill=tk.BOTH, expand=True)

        create_scene_step(self.nb, self)
        create_style_step(self.nb, self)
        create_camera_step(self.nb, self)
        create_output_step(self.nb, self)

        build_preset_tab(self)
        build_params_tab(self)
        build_camera_tab(self)
        build_filter_tab(self)
        build_subject_tab(self)
        build_style_tab(self)
        build_detail_tab(self)
        build_extractor_tab(self)

    # ── 滑条回调 ───────────────────────────────────────────────
    def _on_shot_change(self):
        idx = self.shot_var.get()
        kw, desc = SHOT_SCALE[idx]
        if self.shot_result_label:
            self.shot_result_label.config(text=f"{kw}  ·  {desc}")
        self._generate()

    def _on_elevation_change(self):
        idx = self.elevation_var.get()
        kw, desc = CAMERA_ELEVATION[idx]
        if self.elevation_result_label:
            self.elevation_result_label.config(text=f"{kw}  ·  {desc}")
        self._generate()

    def _on_angle_change(self):
        idx = self.subject_angle_var.get()
        kw, desc = SUBJECT_ANGLE[idx]
        if self.angle_result_label:
            self.angle_result_label.config(text=f"{kw}  ·  {desc}")
        self._generate()


    # ── Entry 占位符 ─────────────────────────────────────────────
    def _entry_focus_in(self, entry):
        if entry.get() == "自定义...":
            entry.delete(0, tk.END)
            entry.config(fg=FG_PRIMARY)

    def _entry_focus_out(self, entry):
        if not entry.get().strip():
            entry.delete(0, tk.END)
            entry.insert(0, "自定义...")
            entry.config(fg=FG_DIM)
        self._generate()

    def _apply_preset(self, name, anime_mode):
        self.is_anime.set(anime_mode)
        self._mode_btn.config(
            text="● 开" if anime_mode else "○ 关",
            bg=ACCENT_PURPLE if anime_mode else BG_HOVER,
            fg=DARK_TEXT if anime_mode else FG_PRIMARY,
        )
        render_params(self)

        preset = (PRESETS_ANIME if anime_mode else PRESETS_REAL)[name]
        params = PARAMS_ANIME if anime_mode else PARAMS_REAL
        resolution = resolve_preset_values(
            preset,
            {pname: data[0] for pname, data in params.items()},
        )
        self.extra_var.set(resolution.extra)

        for pname in self.custom_vars:
            self.custom_vars[pname].set("")

        for pname, value in resolution.param_values.items():
            if pname in self.param_vars:
                self.param_vars[pname].set(value)
        for pname, value in resolution.custom_values.items():
            if pname in self.custom_vars:
                self.custom_vars[pname].set(value)

        self._generate()

    # ── Tab5：主体场景 ────────────────────────────────────────────
    _SUBJECT_HINT = "描述主体（人物/动物/物体）..."
    _ENVIRON_HINT = "描述场景环境（地点/时间/背景）..."

    def _append_chip(self, text_widget, chip):
        current = text_widget.get("1.0", tk.END).strip()
        if current in (self._SUBJECT_HINT, self._ENVIRON_HINT, ""):
            text_widget.config(fg=FG_PRIMARY)
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", chip)
        else:
            text_widget.insert(tk.END, f", {chip}")
        self._generate()

    def _text_focus_in(self, widget, hint):
        if widget.get("1.0", tk.END).strip() == hint:
            widget.delete("1.0", tk.END)
            widget.config(fg=FG_PRIMARY)

    def _text_focus_out(self, widget, hint):
        if not widget.get("1.0", tk.END).strip():
            widget.insert("1.0", hint)
            widget.config(fg=FG_DIM)


    # ── 模式切换 ────────────────────────────────────────────────
    def _toggle_mode(self):
        self.is_anime.set(not self.is_anime.get())
        on = self.is_anime.get()
        self._mode_btn.config(
            text="● 开" if on else "○ 关",
            bg=ACCENT_PURPLE if on else BG_HOVER,
            fg=DARK_TEXT if on else FG_PRIMARY,
        )
        render_params(self)
        refresh_subject_chips(self)
        refresh_style_blocks(self)
        refresh_detail_blocks(self)
        self._generate()

    # ── 右侧预览面板 ─────────────────────────────────────────────

    def _hint_focus_in(self, entry, hint):
        if entry.get() == hint:
            entry.delete(0, tk.END)
            entry.config(fg=FG_PRIMARY)

    def _hint_focus_out(self, entry, hint):
        if not entry.get().strip():
            entry.delete(0, tk.END)
            entry.insert(0, hint)
            entry.config(fg=FG_DIM)

    # ── 生成逻辑 ─────────────────────────────────────────────────


    def _generate(self):
        base_prompt = self._state_collector.build_prompt()
        # 如果"转为正面排除词"开关打开，在正面 prompt 后追加排除段
        if self.neg_to_positive_enabled.get() and self.neg_text is not None:
            neg = self.neg_text.get("1.0", tk.END).strip()
            if neg:
                base_prompt = append_negative_as_positive(base_prompt, neg)

        if self.preview_text is None:
            return
        neg = self._state_collector.negative_text()
        PreviewPanel.render(
            preview_text=self.preview_text,
            preview_zh_text=self.preview_zh_text,
            neg_preview_text=self.neg_preview_text,
            neg_zh_preview_text=self.neg_zh_preview_text,
            prompt=base_prompt,
            prompt_zh=self._state_collector.build_prompt_zh(),
            negative_text=neg,
            negative_zh=self._state_collector.build_negative_zh(neg) if neg else "",
        )

    def _copy(self):
        import pyperclip
        pyperclip.copy(self._state_collector.build_prompt())
        self.title("提示词生成器  ✓ 已复制")
        self.after(2000, lambda: self.title("提示词生成器"))

    def _insert(self):
        prompt = self._state_collector.build_prompt()
        title = tkinter.simpledialog.askstring(
            "保存为 Prompt", "请输入标题：",
            parent=self, initialvalue="📷 摄影机设置",
        )
        if title is None:
            return
        self.on_insert(title.strip() or "📷 摄影机设置", prompt)
        self.destroy()
