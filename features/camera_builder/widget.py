"""
摄影机参数构建器窗口（从 main.py 抽取，依赖 shared/ 和 presets.py）
"""
import math
import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog
from tkinter.colorchooser import askcolor

from shared.ui_kit import (
    bind_mousewheel, make_scroll_canvas, apply_dark_notebook_style, Tooltip,
    BG_BASE, BG_SURFACE, BG_CARD, BG_HOVER,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_YELLOW,
    ACCENT_RED, ACCENT_CYAN, ACCENT_ORANGE, DARK_TEXT,
)
from shared.constants import ZH_PARAM_NAMES, kw_to_zh
from core.services.camera_prompt_service import (
    CameraPromptSpec,
    append_negative_as_positive,
    build_detail_tech_zh as build_detail_tech_zh_text,
    build_camera_prompt,
    build_negative_zh as build_negative_zh_text,
    build_prompt_zh as build_prompt_zh_text,
    build_style_mood_zh as build_style_mood_zh_text,
    build_subject_scene_zh,
    resolve_preset_values,
)
from features.camera_builder.scene_step import create_scene_step
from features.camera_builder.style_step import create_style_step
from features.camera_builder.camera_step import create_camera_step
from features.camera_builder.output_step import create_output_step
from features.camera_builder.preview_panel import PreviewPanel
from features.camera_builder.presets import (
    PARAMS_REAL, PARAMS_ANIME, FILTER_KEYWORDS,
    SHOT_SCALE, CAMERA_ELEVATION, SUBJECT_ANGLE,
    PRESETS_REAL, PRESETS_ANIME,
    SUBJECT_CHIPS_REAL, SUBJECT_CHIPS_ANIME,
    ENVIRONMENT_CHIPS_REAL, ENVIRONMENT_CHIPS_ANIME,
    STYLE_REAL, STYLE_ANIME,
    MOOD_REAL, MOOD_ANIME,
    MOTION_OPTIONS,
    TEXTURE_REAL, TEXTURE_ANIME,
    COLOR_SUPPLEMENT_REAL, COLOR_SUPPLEMENT_ANIME,
    RENDER_ENGINES, OUTPUT_RATIOS,
    WEATHER_CHIPS_REAL, WEATHER_CHIPS_ANIME,
    SUBJECT_COUNT_REAL, SUBJECT_COUNT_ANIME,
    AESTHETIC_REAL, AESTHETIC_ANIME,
    QUALITY_CHIPS_REAL, QUALITY_CHIPS_ANIME,
    NEG_PRESETS,
    NEGATIVE_ZH_MAP, ANIME_STYLE_EXTRACTOR_PRESETS,
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
        self._build_preview_panel(right)

        self.after(20, lambda p=paned: p.sash_place(0, (self.winfo_width() - 32) // 2, 0))

    def _build_notebook(self, parent):
        apply_dark_notebook_style()
        self.nb = ttk.Notebook(parent, style="Dark.TNotebook")
        self.nb.pack(fill=tk.BOTH, expand=True)

        create_scene_step(self.nb, self)
        create_style_step(self.nb, self)
        create_camera_step(self.nb, self)
        create_output_step(self.nb, self)

        self._build_tab_preset()
        self._build_tab_params()
        self._build_tab_camera()
        self._build_tab_filter()
        self._build_tab_subject()
        self._build_tab_style()
        self._build_tab_detail()
        self._build_tab_extractor()

    # ── Tab1：基础参数 ──────────────────────────────────────────
    def _build_tab_params(self):
        self._params_scroll_host = self.tab_params
        self._render_params()

    def _render_params(self):
        for w in self._params_scroll_host.winfo_children():
            w.destroy()
        self.param_vars.clear()
        self.custom_vars.clear()
        self.param_checks.clear()

        params = PARAMS_ANIME if self.is_anime.get() else PARAMS_REAL
        _, inner = make_scroll_canvas(self._params_scroll_host, bg=BG_BASE)

        for name, (options, _) in params.items():
            row = tk.Frame(inner, bg=BG_SURFACE, pady=5)
            row.pack(fill=tk.X, pady=2, padx=4)

            enabled = tk.BooleanVar(value=True)
            self.param_checks[name] = enabled
            tk.Checkbutton(row, variable=enabled, bg=BG_SURFACE, activebackground=BG_SURFACE,
                           selectcolor=BG_HOVER, fg=FG_PRIMARY,
                           command=self._generate).pack(side=tk.LEFT, padx=(6, 0))

            tk.Label(row, text=name, bg=BG_SURFACE, fg=FG_PRIMARY,
                     font=("微软雅黑", 9, "bold"), width=10, anchor="w").pack(side=tk.LEFT, padx=(4, 8))

            selected_sv = tk.StringVar(value=options[0])
            self.param_vars[name] = selected_sv
            cb = ttk.Combobox(row, textvariable=selected_sv, values=options,
                              state="readonly", width=28, font=("微软雅黑", 9))
            cb.pack(side=tk.LEFT, padx=(0, 8))
            cb.bind("<<ComboboxSelected>>", lambda _e: self._generate())

            custom_sv = tk.StringVar()
            self.custom_vars[name] = custom_sv
            entry = tk.Entry(row, textvariable=custom_sv, bg=BG_CARD, fg=FG_PRIMARY,
                             insertbackground=FG_PRIMARY, relief=tk.FLAT,
                             font=("微软雅黑", 9), width=20)
            entry.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
            entry.insert(0, "自定义...")
            entry.config(fg=FG_DIM)
            entry.bind("<FocusIn>",  lambda _e, ent=entry: self._entry_focus_in(ent))
            entry.bind("<FocusOut>", lambda _e, ent=entry: self._entry_focus_out(ent))
            entry.bind("<KeyRelease>", lambda _e: self._generate())

    # ── Tab2：镜头位置 ─────────────────────────────────────────
    def _build_tab_camera(self):
        _, inner = make_scroll_canvas(self.tab_camera, bg=BG_SURFACE)
        self._build_sliders_section(inner)

    def _build_sliders_section(self, parent):
        outer = tk.Frame(parent, bg=BG_SURFACE)
        outer.pack(fill=tk.BOTH, expand=True)

        def _slider_section(title, var, enabled_var, labels, lo, hi, color,
                            on_change_fn, result_label_attr):
            sec = tk.Frame(outer, bg=BG_SURFACE)
            sec.pack(fill=tk.X, padx=16, pady=(10, 6))

            hdr = tk.Frame(sec, bg=BG_SURFACE)
            hdr.pack(fill=tk.X)
            tk.Label(hdr, text=title, bg=BG_SURFACE, fg=FG_PRIMARY,
                     font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
            tk.Checkbutton(hdr, text="加入生成结果", variable=enabled_var,
                           bg=BG_SURFACE, fg=FG_MUTED, activebackground=BG_SURFACE,
                           selectcolor=BG_HOVER, font=("微软雅黑", 8),
                           command=self._generate).pack(side=tk.RIGHT)

            lbl_row = tk.Frame(sec, bg=BG_SURFACE)
            lbl_row.pack(fill=tk.X, pady=(6, 0))
            for t in labels:
                tk.Label(lbl_row, text=t, bg=BG_SURFACE, fg=FG_MUTED,
                         font=("微软雅黑", 8), width=5).pack(side=tk.LEFT, expand=True)

            tk.Scale(sec, from_=lo, to=hi, orient=tk.HORIZONTAL, variable=var,
                     showvalue=False, bg=BG_SURFACE, fg=color, troughcolor=BG_CARD,
                     activebackground=color, highlightthickness=0, resolution=1,
                     command=lambda _v: on_change_fn()).pack(fill=tk.X, pady=(0, 2))

            lbl = tk.Label(sec, text="", bg=BG_SURFACE, fg=color,
                           font=("微软雅黑", 9))
            lbl.pack(anchor="w")
            setattr(self, result_label_attr, lbl)
            ttk.Separator(outer, orient="horizontal").pack(fill=tk.X, padx=16, pady=6)

        _slider_section(
            "🔭 景别 Shot Scale", self.shot_var, self.shot_enabled,
            ["超远景", "远景", "中景", "近景", "特写", "微距", "超微距"], 0, 6,
            ACCENT_PURPLE, self._on_shot_change, "shot_result_label",
        )
        _slider_section(
            "📐 俯仰角 Camera Elevation", self.elevation_var, self.elevation_enabled,
            ["极端仰", "仰拍", "轻仰", "平视", "轻俯", "俯拍", "顶视"], 0, 6,
            ACCENT_YELLOW, self._on_elevation_change, "elevation_result_label",
        )
        _slider_section(
            "🧭 主体方位角 Subject Angle", self.subject_angle_var, self.subject_angle_enabled,
            ["正面", "左前", "左侧", "左后", "背面", "右后", "右侧", "右前"], 0, 7,
            ACCENT_CYAN, self._on_angle_change, "angle_result_label",
        )

        self._on_shot_change()
        self._on_elevation_change()
        self._on_angle_change()

        # ── 主光源 ──
        sec3 = tk.Frame(outer, bg=BG_SURFACE)
        sec3.pack(fill=tk.X, padx=16, pady=(0, 6))
        hdr3 = tk.Frame(sec3, bg=BG_SURFACE)
        hdr3.pack(fill=tk.X)
        tk.Label(hdr3, text="💡 主光源 Key Light", bg=BG_SURFACE, fg=FG_PRIMARY,
                 font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
        tk.Checkbutton(hdr3, text="加入生成结果", variable=self.light_dir_enabled,
                       bg=BG_SURFACE, fg=FG_MUTED, activebackground=BG_SURFACE,
                       selectcolor=BG_HOVER, font=("微软雅黑", 8),
                       command=self._generate).pack(side=tk.RIGHT)

        light_body = tk.Frame(sec3, bg=BG_SURFACE)
        light_body.pack(fill=tk.X, pady=(8, 0))

        SPHERE_SIZE = 160
        self._light_sphere_canvas = tk.Canvas(
            light_body, width=SPHERE_SIZE, height=SPHERE_SIZE,
            bg="#1a1a2e", highlightthickness=1, highlightbackground=BG_HOVER,
            cursor="crosshair",
        )
        self._light_sphere_canvas.pack(side=tk.LEFT, padx=(0, 12))
        self._draw_light_sphere()
        self._light_sphere_canvas.bind("<Button-1>",        self._sphere_click)
        self._light_sphere_canvas.bind("<B1-Motion>",       self._sphere_drag)
        self._light_sphere_canvas.bind("<ButtonRelease-1>", self._sphere_release)

        right_col = tk.Frame(light_body, bg=BG_SURFACE)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        hemi_row = tk.Frame(right_col, bg=BG_SURFACE)
        hemi_row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(hemi_row, text="视角面:", bg=BG_SURFACE, fg=FG_MUTED,
                 font=("微软雅黑", 8)).pack(side=tk.LEFT)
        self._hemi_front_btn = tk.Button(
            hemi_row, text="前", bg=ACCENT_BLUE, fg=DARK_TEXT,
            relief=tk.FLAT, font=("微软雅黑", 8, "bold"), padx=8, pady=2,
            cursor="hand2", activebackground=ACCENT_BLUE,
            command=lambda: self._set_hemi(False),
        )
        self._hemi_front_btn.pack(side=tk.LEFT, padx=(6, 2))
        self._hemi_back_btn = tk.Button(
            hemi_row, text="后", bg=BG_HOVER, fg=FG_PRIMARY,
            relief=tk.FLAT, font=("微软雅黑", 8, "bold"), padx=8, pady=2,
            cursor="hand2", activebackground=BG_HOVER,
            command=lambda: self._set_hemi(True),
        )
        self._hemi_back_btn.pack(side=tk.LEFT)

        color_row = tk.Frame(right_col, bg=BG_SURFACE)
        color_row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(color_row, text="光源颜色", bg=BG_SURFACE, fg=FG_MUTED,
                 font=("微软雅黑", 8)).pack(side=tk.LEFT)
        self._light_color_btn = tk.Button(
            color_row, text="", width=3, relief=tk.FLAT, cursor="hand2",
            bg=self.light_color, activebackground=self.light_color,
            command=self._pick_light_color,
        )
        self._light_color_btn.pack(side=tk.LEFT, padx=(8, 0), ipady=6)
        self._light_color_label = tk.Label(
            color_row, text=self.light_color, bg=BG_SURFACE, fg=FG_MUTED,
            font=("微软雅黑", 8),
        )
        self._light_color_label.pack(side=tk.LEFT, padx=(6, 0))

        self._azimuth_label = tk.Label(right_col, text="", bg=BG_SURFACE,
                                       fg=ACCENT_YELLOW, font=("微软雅黑", 8))
        self._azimuth_label.pack(anchor="w", pady=(0, 2))
        self._elev_label = tk.Label(right_col, text="", bg=BG_SURFACE,
                                    fg=ACCENT_YELLOW, font=("微软雅黑", 8))
        self._elev_label.pack(anchor="w", pady=(0, 2))
        self._light_kw_label = tk.Label(right_col, text="", bg=BG_SURFACE,
                                        fg=ACCENT_GREEN, font=("微软雅黑", 8),
                                        wraplength=160, justify=tk.LEFT)
        self._light_kw_label.pack(anchor="w")
        self._update_light_labels()

        ttk.Separator(outer, orient="horizontal").pack(fill=tk.X, padx=16, pady=6)

        # ── 轮廓光 ──
        sec4 = tk.Frame(outer, bg=BG_SURFACE)
        sec4.pack(fill=tk.X, padx=16, pady=(0, 12))
        tk.Label(sec4, text="✨ 轮廓光 Rim Light", bg=BG_SURFACE, fg=FG_PRIMARY,
                 font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
        self._rim_btn = tk.Button(
            sec4, text="○ 关", bg=BG_HOVER, fg=FG_PRIMARY,
            relief=tk.FLAT, font=("微软雅黑", 9, "bold"), padx=10, pady=2,
            cursor="hand2", command=self._toggle_rim_light,
        )
        self._rim_btn.pack(side=tk.RIGHT)

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

    def _toggle_rim_light(self):
        self.rim_light_var.set(not self.rim_light_var.get())
        on = self.rim_light_var.get()
        self._rim_btn.config(
            text="● 开" if on else "○ 关",
            bg=ACCENT_YELLOW if on else BG_HOVER,
            fg=DARK_TEXT if on else FG_PRIMARY,
        )
        self._generate()

    # ── 3D 球体光源 ─────────────────────────────────────────────
    _SPHERE_R    = 68
    _SPHERE_SIZE = 160

    def _sphere_xy_from_angles(self):
        cx = cy = self._SPHERE_SIZE / 2
        az = math.radians(self.light_azimuth.get())
        el = math.radians(self.light_elevation.get())
        x = cx + self._SPHERE_R * math.sin(az) * math.cos(el)
        y = cy - self._SPHERE_R * math.sin(el)
        return x, y

    def _angles_from_sphere_xy(self, mx, my):
        cx = cy = self._SPHERE_SIZE / 2
        dx = mx - cx
        dy = -(my - cy)
        dist = math.hypot(dx, dy)
        r = self._SPHERE_R
        if dist > r:
            scale = r / dist
            dx *= scale
            dy *= scale
        el = math.degrees(math.asin(max(-1, min(1, dy / r))))
        cos_el = math.cos(math.radians(el))
        if cos_el > 1e-6:
            sin_az = max(-1.0, min(1.0, dx / (r * cos_el)))
            az_raw = math.degrees(math.asin(sin_az))
            if self.light_back_mode.get():
                az = (180.0 - az_raw) % 360
            else:
                az = az_raw % 360
        else:
            az = self.light_azimuth.get()
        return az, el

    def _draw_light_sphere(self):
        c = self._light_sphere_canvas
        if c is None:
            return
        c.delete("all")
        cx = cy = self._SPHERE_SIZE / 2
        r = self._SPHERE_R

        for i in range(4, 0, -1):
            rr = r * i / 4
            grey = 30 + i * 8
            col = f"#{grey:02x}{grey:02x}{grey+10:02x}"
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline="", fill=col)

        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=BG_HOVER, width=1, fill="")

        for az_deg in range(0, 180, 45):
            az = math.radians(az_deg)
            pts = []
            for el_deg in range(-90, 91, 5):
                el = math.radians(el_deg)
                pts.extend([cx + r * math.sin(az) * math.cos(el), cy - r * math.sin(el)])
            if len(pts) >= 4:
                c.create_line(pts, fill="#2a2a4a", width=1, smooth=True)
            pts2 = []
            for el_deg in range(-90, 91, 5):
                el = math.radians(el_deg)
                pts2.extend([cx - r * math.sin(az) * math.cos(el), cy - r * math.sin(el)])
            if len(pts2) >= 4:
                c.create_line(pts2, fill="#2a2a4a", width=1, smooth=True)

        for el_deg in [-60, -30, 0, 30, 60]:
            el = math.radians(el_deg)
            ry = r * math.cos(el)
            yy = cy - r * math.sin(el)
            col = "#3a3a5a" if el_deg != 0 else "#4a4a6a"
            c.create_oval(cx - ry, yy - ry * 0.15, cx + ry, yy + ry * 0.15, outline=col, width=1, fill="")

        c.create_oval(cx - r, cy - r * 0.15, cx + r, cy + r * 0.15, outline="#55557a", width=1, fill="")

        lx, ly = self._sphere_xy_from_angles()
        c.create_line(cx, cy, lx, ly, fill=ACCENT_YELLOW, width=1, dash=(3, 3))

        dot_r = 7
        col = self.light_color or "#ffffff"
        for halo in [14, 10]:
            alpha_col = self._blend_color(col, "#1a1a2e", halo / 14)
            c.create_oval(lx - halo, ly - halo, lx + halo, ly + halo, outline="", fill=alpha_col)
        c.create_oval(lx - dot_r, ly - dot_r, lx + dot_r, ly + dot_r,
                      outline="#ffffff", width=1, fill=col, tags="dot")
        self._light_dot_id = "dot"

    def _blend_color(self, hex1, hex2, t):
        def parse(h):
            h = h.lstrip("#")
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r1, g1, b1 = parse(hex1)
        r2, g2, b2 = parse(hex2)
        return f"#{int(r1*t+r2*(1-t)):02x}{int(g1*t+g2*(1-t)):02x}{int(b1*t+b2*(1-t)):02x}"

    def _sphere_click(self, event):
        az, el = self._angles_from_sphere_xy(event.x, event.y)
        self.light_azimuth.set(round(az, 1))
        self.light_elevation.set(round(el, 1))
        self._draw_light_sphere()
        self._update_light_labels()
        self._generate()

    def _sphere_drag(self, event):
        self._sphere_click(event)

    def _sphere_release(self, event):
        self._sphere_click(event)

    def _update_light_labels(self):
        az = self.light_azimuth.get()
        el = self.light_elevation.get()
        if self._azimuth_label:
            self._azimuth_label.config(text=f"水平角: {az:.0f}°")
        if self._elev_label:
            self._elev_label.config(text=f"仰俯角: {el:.0f}°")
        if self._light_kw_label:
            self._light_kw_label.config(text=self._light_keyword())

    def _light_keyword(self):
        az = self.light_azimuth.get()
        el = self.light_elevation.get()

        if el > 60:
            dir_str = "overhead top-down lighting"
        elif el < -60:
            dir_str = "underlighting from below"
        else:
            sectors = [
                (0,   22,  "front lighting"),
                (22,  68,  "front-right lighting"),
                (68,  112, "right side lighting"),
                (112, 158, "back-right lighting"),
                (158, 202, "back lighting"),
                (202, 248, "back-left lighting"),
                (248, 292, "left side lighting"),
                (292, 338, "front-left lighting"),
                (338, 360, "front lighting"),
            ]
            dir_str = "front lighting"
            for lo, hi, name in sectors:
                if lo <= az < hi:
                    dir_str = name
                    break
            if el > 30:
                dir_str = "high " + dir_str
            elif el < -15:
                dir_str = "low " + dir_str

        color_map = {
            "#ffffff": "white", "#fff4e0": "warm white", "#ffd700": "golden",
            "#ff8c00": "orange", "#ff4500": "red-orange", "#ff0000": "red",
            "#ff69b4": "pink", "#00bfff": "cool blue", "#87ceeb": "soft blue",
            "#00ffff": "cyan", "#00ff00": "green", "#9400d3": "purple",
        }
        col_str = color_map.get(self.light_color.lower())
        if col_str is None:
            import colorsys
            def hex_to_rgb(h):
                h = h.lstrip("#")
                return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
            def color_dist(h1, h2):
                r1, g1, b1 = hex_to_rgb(h1)
                r2, g2, b2 = hex_to_rgb(h2)
                return (r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2
            best = min(color_map.keys(), key=lambda k: color_dist(k, self.light_color.lower()))
            if color_dist(best, self.light_color.lower()) < 0.15:
                col_str = color_map[best]
            else:
                r, g, b = hex_to_rgb(self.light_color.lower())
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                if s < 0.15:
                    col_str = "white" if v > 0.8 else "grey"
                else:
                    hue_names = [(0, "red"), (30/360, "orange"), (60/360, "yellow"),
                                 (120/360, "green"), (180/360, "cyan"), (240/360, "blue"),
                                 (300/360, "purple"), (330/360, "pink"), (1.0, "red")]
                    col_str = min(hue_names, key=lambda x: abs(x[0]-h))[1]

        if col_str in {"white", "warm white"}:
            return dir_str
        return f"{col_str} {dir_str}"

    def _pick_light_color(self):
        result = askcolor(color=self.light_color, parent=self, title="选择光源颜色")
        if result and result[1]:
            self.light_color = result[1].lower()
            if self._light_color_btn:
                self._light_color_btn.config(bg=self.light_color, activebackground=self.light_color)
            if self._light_color_label:
                self._light_color_label.config(text=self.light_color)
            self._draw_light_sphere()
            self._update_light_labels()
            self._generate()

    def _set_hemi(self, back: bool):
        self.light_back_mode.set(back)
        if self._hemi_front_btn:
            self._hemi_front_btn.config(
                bg=ACCENT_BLUE if not back else BG_HOVER,
                fg=DARK_TEXT if not back else FG_PRIMARY,
            )
        if self._hemi_back_btn:
            self._hemi_back_btn.config(
                bg=ACCENT_BLUE if back else BG_HOVER,
                fg=DARK_TEXT if back else FG_PRIMARY,
            )
        az = self.light_azimuth.get()
        if back and not (90 <= az <= 270):
            self.light_azimuth.set((180 - az) % 360)
        elif not back and (90 < az < 270):
            self.light_azimuth.set((180 - az) % 360)
        self._draw_light_sphere()
        self._update_light_labels()
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

    # ── Tab3：滤镜积木 ────────────────────────────────────────────
    def _build_tab_filter(self):
        self.filter_toggles.clear()
        self.filter_labels.clear()
        self.filter_custom_vars.clear()

        _, inner = make_scroll_canvas(self.tab_filter, bg=BG_BASE)
        tk.Label(inner, text="点击关键词选中（高亮），再点取消。每组下方可添加自定义词块。",
                 bg=BG_BASE, fg=FG_DIM, font=("微软雅黑", 8)).pack(anchor="w", padx=10, pady=(8, 4))

        for category, words in FILTER_KEYWORDS.items():
            self._make_filter_group(inner, category, words)

    def _make_filter_group(self, parent, category, words):
        group = tk.Frame(parent, bg=BG_BASE)
        group.pack(fill=tk.X, padx=10, pady=(6, 2))

        tk.Label(group, text=category, bg=BG_BASE, fg=ACCENT_PURPLE,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w")

        btn_grid = tk.Frame(group, bg=BG_BASE)
        btn_grid.pack(fill=tk.X, pady=(4, 0))

        row_idx, col_idx, cols = 0, 0, 3
        for display_label, english_keyword in words:
            bv = tk.BooleanVar(value=False)
            self.filter_toggles[english_keyword] = bv
            self.filter_labels[english_keyword] = display_label
            btn = self._make_toggle_btn(btn_grid, display_label, english_keyword, bv)
            btn_grid.grid_columnconfigure(col_idx, weight=1)
            btn.grid(row=row_idx, column=col_idx, padx=3, pady=2, sticky="ew")
            col_idx += 1
            if col_idx >= cols:
                col_idx = 0
                row_idx += 1

        custom_row = tk.Frame(group, bg=BG_BASE)
        custom_row.pack(fill=tk.X, pady=(6, 0))
        sv = tk.StringVar()
        self.filter_custom_vars[category] = sv
        HINT = "自定义词块：中文 / english keyword"
        entry = tk.Entry(custom_row, textvariable=sv, bg=BG_CARD, fg=FG_DIM,
                         insertbackground=FG_PRIMARY, relief=tk.FLAT, font=("微软雅黑", 9))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        entry.insert(0, HINT)
        entry.bind("<FocusIn>",  lambda _e, ent=entry, h=HINT: self._hint_focus_in(ent, h))
        entry.bind("<FocusOut>", lambda _e, ent=entry, h=HINT: self._hint_focus_out(ent, h))
        tk.Button(custom_row, text="+ 添加", bg=ACCENT_BLUE, fg=DARK_TEXT, relief=tk.FLAT,
                  font=("微软雅黑", 8, "bold"), padx=10, pady=3, cursor="hand2",
                  activebackground=ACCENT_BLUE,
                  command=lambda bg=btn_grid, ent=entry, ri=[row_idx], ci=[col_idx], co=cols:
                      self._add_custom_filter_btn(bg, ent, ri, ci, co)
                  ).pack(side=tk.LEFT, padx=(6, 0))

    def _make_toggle_btn(self, parent, display_label, english_keyword, bv):
        btn_ref = [None]
        def toggle():
            bv.set(not bv.get())
            btn_ref[0].config(
                bg=ACCENT_PURPLE if bv.get() else BG_CARD,
                fg=DARK_TEXT if bv.get() else FG_PRIMARY,
            )
            self._generate()
        b = tk.Button(parent, text=display_label, bg=BG_CARD, fg=FG_PRIMARY,
                      relief=tk.FLAT, font=("微软雅黑", 8), padx=8, pady=6,
                      cursor="hand2", activebackground=BG_HOVER,
                      wraplength=170, justify=tk.LEFT, command=toggle)
        btn_ref[0] = b
        Tooltip(b, f"英文关键词：{english_keyword}\n点击选中（高亮），再点取消。选中后加入生成结果。")
        return b

    def _add_custom_filter_btn(self, grid_frame, entry, row_idx_ref, col_idx_ref, cols):
        HINT = "自定义词块：中文 / english keyword"
        raw = entry.get().strip()
        if not raw or raw == HINT:
            return
        if "/" in raw:
            display_label = raw
            english_keyword = raw.split("/")[-1].strip()
        else:
            display_label = raw
            english_keyword = raw
        if english_keyword in self.filter_toggles:
            return
        bv = tk.BooleanVar(value=True)
        self.filter_toggles[english_keyword] = bv
        self.filter_labels[english_keyword] = display_label
        btn = self._make_toggle_btn(grid_frame, display_label, english_keyword, bv)
        btn.config(bg=ACCENT_PURPLE, fg=DARK_TEXT)
        ri, ci = row_idx_ref[0], col_idx_ref[0]
        grid_frame.grid_columnconfigure(ci, weight=1)
        btn.grid(row=ri, column=ci, padx=3, pady=2, sticky="ew")
        col_idx_ref[0] += 1
        if col_idx_ref[0] >= cols:
            col_idx_ref[0] = 0
            row_idx_ref[0] += 1
        entry.delete(0, tk.END)
        entry.insert(0, HINT)
        entry.config(fg=FG_DIM)
        self._generate()

    # ── Tab4：预设 ────────────────────────────────────────────────
    def _build_tab_preset(self):
        _, inner = make_scroll_canvas(self.tab_preset, bg=BG_BASE)

        tk.Label(inner, text="🎬 经典电影预设（实拍模式）", bg=BG_BASE, fg=ACCENT_BLUE,
                 font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
        self._make_preset_grid(inner, PRESETS_REAL, anime_mode=False)

        ttk.Separator(inner, orient="horizontal").pack(fill=tk.X, padx=12, pady=12)

        tk.Label(inner, text="🌸 动画风格预设（二次元模式）", bg=BG_BASE, fg=ACCENT_PURPLE,
                 font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=12, pady=(0, 6))
        self._make_preset_grid(inner, PRESETS_ANIME, anime_mode=True)

        ttk.Separator(inner, orient="horizontal").pack(fill=tk.X, padx=12, pady=12)
        tk.Label(inner, text="💡 点击预设会自动切换模式并填充参数，之后可在参数页微调。",
                 bg=BG_BASE, fg=FG_DIM, font=("微软雅黑", 9)).pack(anchor="w", padx=12, pady=(0, 12))

    def _make_preset_grid(self, parent, presets_dict, anime_mode):
        from features.camera_builder.presets import PRESETS_REAL, PRESETS_ANIME
        grid = tk.Frame(parent, bg=BG_BASE)
        grid.pack(fill=tk.X, padx=12, pady=(0, 4))
        cols, row_idx, col_idx = 3, 0, 0
        preset_data = PRESETS_ANIME if anime_mode else PRESETS_REAL
        for name in presets_dict:
            grid.grid_columnconfigure(col_idx, weight=1)
            pdata = preset_data.get(name, {})
            tip_parts = [f"🎬 {name}"]
            if "_extra" in pdata:
                tip_parts.append(f"风格词：{pdata['_extra'][:60]}…")
            tip_parts.append("点击应用此预设，自动填充所有参数。")
            b = tk.Button(
                grid, text=name, bg=BG_CARD, fg=FG_PRIMARY,
                relief=tk.FLAT, font=("微软雅黑", 9), padx=10, pady=10,
                cursor="hand2", activebackground=BG_HOVER,
                wraplength=200, justify=tk.LEFT,
                command=lambda n=name, a=anime_mode: self._apply_preset(n, a),
            )
            b.grid(row=row_idx, column=col_idx, padx=4, pady=3, sticky="ew")
            Tooltip(b, "\n".join(tip_parts))
            col_idx += 1
            if col_idx >= cols:
                col_idx = 0
                row_idx += 1

    def _apply_preset(self, name, anime_mode):
        self.is_anime.set(anime_mode)
        self._mode_btn.config(
            text="● 开" if anime_mode else "○ 关",
            bg=ACCENT_PURPLE if anime_mode else BG_HOVER,
            fg=DARK_TEXT if anime_mode else FG_PRIMARY,
        )
        self._render_params()

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

    def _build_tab_subject(self):
        _, inner = make_scroll_canvas(self.tab_subject, bg=BG_BASE)

        # ── 主体描述 ─────────────────────────────────────────────
        tk.Label(inner, text="✍ 主体描述", bg=BG_BASE, fg=ACCENT_CYAN,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 2))

        self.subject_text = tk.Text(inner, bg=BG_CARD, fg=FG_PRIMARY,
                                    insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                    font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
                                    height=3)
        self.subject_text.pack(fill=tk.X, padx=10, pady=(0, 4))
        self.subject_text.insert("1.0", self._SUBJECT_HINT)
        self.subject_text.config(fg=FG_DIM)
        self.subject_text.bind("<FocusIn>",  lambda _e: self._text_focus_in(self.subject_text, self._SUBJECT_HINT))
        self.subject_text.bind("<FocusOut>", lambda _e: self._text_focus_out(self.subject_text, self._SUBJECT_HINT))
        self.subject_text.bind("<KeyRelease>", lambda _e: self._generate())

        # 主体快捷词块
        tk.Label(inner, text="角色词块:", bg=BG_BASE, fg=FG_DIM,
                 font=("微软雅黑", 8)).pack(anchor="w", padx=10)
        self._subject_chips_frame = tk.Frame(inner, bg=BG_BASE)
        self._subject_chips_frame.pack(fill=tk.X, padx=10, pady=(2, 4))
        self._fill_chips(self._subject_chips_frame, self.subject_text,
                         SUBJECT_CHIPS_ANIME if self.is_anime.get() else SUBJECT_CHIPS_REAL)

        # 人数词块
        tk.Label(inner, text="人数/关系:", bg=BG_BASE, fg=FG_DIM,
                 font=("微软雅黑", 8)).pack(anchor="w", padx=10)
        self._count_chips_frame = tk.Frame(inner, bg=BG_BASE)
        self._count_chips_frame.pack(fill=tk.X, padx=10, pady=(2, 10))
        self._fill_chips(self._count_chips_frame, self.subject_text,
                         SUBJECT_COUNT_ANIME if self.is_anime.get() else SUBJECT_COUNT_REAL)

        # ── 场景环境 ─────────────────────────────────────────────
        tk.Label(inner, text="🌍 场景环境", bg=BG_BASE, fg=ACCENT_CYAN,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 2))

        self.environ_text = tk.Text(inner, bg=BG_CARD, fg=FG_PRIMARY,
                                    insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                    font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
                                    height=3)
        self.environ_text.pack(fill=tk.X, padx=10, pady=(0, 4))
        self.environ_text.insert("1.0", self._ENVIRON_HINT)
        self.environ_text.config(fg=FG_DIM)
        self.environ_text.bind("<FocusIn>",  lambda _e: self._text_focus_in(self.environ_text, self._ENVIRON_HINT))
        self.environ_text.bind("<FocusOut>", lambda _e: self._text_focus_out(self.environ_text, self._ENVIRON_HINT))
        self.environ_text.bind("<KeyRelease>", lambda _e: self._generate())

        # 场景快捷词块
        tk.Label(inner, text="场景词块:", bg=BG_BASE, fg=FG_DIM,
                 font=("微软雅黑", 8)).pack(anchor="w", padx=10)
        self._environ_chips_frame = tk.Frame(inner, bg=BG_BASE)
        self._environ_chips_frame.pack(fill=tk.X, padx=10, pady=(2, 4))
        self._fill_chips(self._environ_chips_frame, self.environ_text,
                         ENVIRONMENT_CHIPS_ANIME if self.is_anime.get() else ENVIRONMENT_CHIPS_REAL)

        # 时间/天气词块
        tk.Label(inner, text="时间/天气:", bg=BG_BASE, fg=FG_DIM,
                 font=("微软雅黑", 8)).pack(anchor="w", padx=10)
        self._weather_chips_frame = tk.Frame(inner, bg=BG_BASE)
        self._weather_chips_frame.pack(fill=tk.X, padx=10, pady=(2, 10))
        self._fill_chips(self._weather_chips_frame, self.environ_text,
                         WEATHER_CHIPS_ANIME if self.is_anime.get() else WEATHER_CHIPS_REAL)

    def _fill_chips(self, frame, target_text, chips):
        for w in frame.winfo_children():
            w.destroy()
        for chip in chips:
            if isinstance(chip, tuple):
                english, chinese = chip
                display = f"{chinese}\n{english}"
                output = english
            else:
                display = chip
                output = chip
            b = tk.Button(
                frame, text=display, bg=BG_CARD, fg=FG_PRIMARY, relief=tk.FLAT,
                font=("微软雅黑", 8), padx=8, pady=4, cursor="hand2",
                activebackground=BG_HOVER, wraplength=120, justify=tk.CENTER,
                command=lambda c=output, t=target_text: self._append_chip(t, c),
            )
            b.pack(side=tk.LEFT, padx=(0, 4), pady=2)
            if isinstance(chip, tuple):
                Tooltip(b, f"{chinese}\n英文：{output}\n点击追加到文本框。")
            else:
                Tooltip(b, f"{output}\n点击追加到文本框。")

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

    def _refresh_subject_chips(self):
        if self._subject_chips_frame and self._subject_chips_frame.winfo_exists():
            self._fill_chips(self._subject_chips_frame, self.subject_text,
                             SUBJECT_CHIPS_ANIME if self.is_anime.get() else SUBJECT_CHIPS_REAL)
        if self._count_chips_frame and self._count_chips_frame.winfo_exists():
            self._fill_chips(self._count_chips_frame, self.subject_text,
                             SUBJECT_COUNT_ANIME if self.is_anime.get() else SUBJECT_COUNT_REAL)
        if self._environ_chips_frame and self._environ_chips_frame.winfo_exists():
            self._fill_chips(self._environ_chips_frame, self.environ_text,
                             ENVIRONMENT_CHIPS_ANIME if self.is_anime.get() else ENVIRONMENT_CHIPS_REAL)
        if self._weather_chips_frame and self._weather_chips_frame.winfo_exists():
            self._fill_chips(self._weather_chips_frame, self.environ_text,
                             WEATHER_CHIPS_ANIME if self.is_anime.get() else WEATHER_CHIPS_REAL)

    # ── Tab6：风格情绪 ────────────────────────────────────────────
    def _build_tab_style(self):
        _, inner = make_scroll_canvas(self.tab_style, bg=BG_BASE)

        tk.Label(inner, text="🎨 风格", bg=BG_BASE, fg=ACCENT_BLUE,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
        self._style_grid = tk.Frame(inner, bg=BG_BASE)
        self._style_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._fill_toggle_grid(self._style_grid, self.style_toggles,
                               STYLE_ANIME if self.is_anime.get() else STYLE_REAL, cols=4)

        tk.Label(inner, text="🏛 美学流派", bg=BG_BASE, fg=ACCENT_PURPLE,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
        self._aesthetic_grid = tk.Frame(inner, bg=BG_BASE)
        self._aesthetic_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._fill_toggle_grid(self._aesthetic_grid, self.aesthetic_toggles,
                               AESTHETIC_ANIME if self.is_anime.get() else AESTHETIC_REAL, cols=4)

        tk.Label(inner, text="💫 情绪氛围", bg=BG_BASE, fg=ACCENT_YELLOW,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
        self._mood_grid = tk.Frame(inner, bg=BG_BASE)
        self._mood_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._fill_toggle_grid(self._mood_grid, self.mood_toggles,
                               MOOD_ANIME if self.is_anime.get() else MOOD_REAL, cols=4)

        motion_row = tk.Frame(inner, bg=BG_BASE)
        motion_row.pack(fill=tk.X, padx=10, pady=(6, 10))
        tk.Label(motion_row, text="🏃 动作/动态:", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)

        _MOTION_ZH = {
            "（不指定）": "（不指定）",
            "walking slowly": "缓步行走",
            "running at full speed": "全速奔跑",
            "jumping mid-air": "腾空跳跃",
            "standing still, slight breeze": "静立，微风轻抚",
            "dancing gracefully": "优雅起舞",
            "reaching out hand": "伸手向前",
            "looking back over shoulder": "回眸望向肩后",
            "crouching low": "低身蹲伏",
            "falling": "坠落",
            "floating": "漂浮",
            "sitting cross-legged": "盘腿而坐",
            "kneeling": "单膝跪地",
            "lying down": "平躺",
            "looking up at sky": "仰望天空",
            "arms raised": "双臂举起",
        }

        ttk.Combobox(motion_row, textvariable=self.motion_var, values=MOTION_OPTIONS,
                     state="readonly", width=28, font=("微软雅黑", 9)
                     ).pack(side=tk.LEFT, padx=(8, 0), ipady=3)
        self._motion_zh_lbl = tk.Label(motion_row, text="", bg=BG_BASE, fg=FG_MUTED,
                                       font=("微软雅黑", 8))
        self._motion_zh_lbl.pack(side=tk.LEFT, padx=(8, 0))

        def _update_motion_zh(*_):
            zh = _MOTION_ZH.get(self.motion_var.get(), "")
            self._motion_zh_lbl.config(text=f"（{zh}）" if zh and zh != "（不指定）" else "")
            self._generate()

        self.motion_var.trace_add("write", _update_motion_zh)

    def _fill_toggle_grid(self, grid_frame, toggles_dict, data, cols=4):
        # 保留已�� BoolVar 的状态（供风格提炼器等外部设置使用）
        saved_state = {kw: bv.get() for kw, bv in toggles_dict.items()}
        for w in grid_frame.winfo_children():
            w.destroy()
        toggles_dict.clear()
        for c in range(cols):
            grid_frame.grid_columnconfigure(c, weight=1)
        for idx, (kw, zh) in enumerate(data):
            bv = tk.BooleanVar(value=saved_state.get(kw, False))
            toggles_dict[kw] = bv
            row_i, col_i = divmod(idx, cols)
            btn_ref = [None]
            display = f"{kw}\n{zh}"

            def _toggle(b=bv, br=btn_ref):
                b.set(not b.get())
                br[0].config(bg=ACCENT_BLUE if b.get() else BG_CARD,
                             fg=DARK_TEXT if b.get() else FG_PRIMARY)
                self._generate()

            btn = tk.Button(grid_frame, text=display, bg=BG_CARD, fg=FG_PRIMARY,
                            relief=tk.FLAT, font=("微软雅黑", 8), padx=8, pady=6,
                            cursor="hand2", activebackground=BG_HOVER,
                            wraplength=130, justify=tk.CENTER, command=_toggle)
            btn_ref[0] = btn
            btn.grid(row=row_i, column=col_i, padx=3, pady=2, sticky="ew")
            Tooltip(btn, f"{zh}\n{kw}\n点击选中/取消，选中后加入生成结果。")

    def _refresh_style_blocks(self):
        if self._style_grid and self._style_grid.winfo_exists():
            self._fill_toggle_grid(self._style_grid, self.style_toggles,
                                   STYLE_ANIME if self.is_anime.get() else STYLE_REAL, cols=4)
        if self._aesthetic_grid and self._aesthetic_grid.winfo_exists():
            self._fill_toggle_grid(self._aesthetic_grid, self.aesthetic_toggles,
                                   AESTHETIC_ANIME if self.is_anime.get() else AESTHETIC_REAL, cols=4)
        if self._mood_grid and self._mood_grid.winfo_exists():
            self._fill_toggle_grid(self._mood_grid, self.mood_toggles,
                                   MOOD_ANIME if self.is_anime.get() else MOOD_REAL, cols=4)

    # ── Tab7：细节技术 ────────────────────────────────────────────
    def _build_tab_detail(self):
        _, inner = make_scroll_canvas(self.tab_detail, bg=BG_BASE)

        # ── 质量词块 ─────────────────────────────────────────────
        tk.Label(inner, text="⭐ 质量词块", bg=BG_BASE, fg=ACCENT_YELLOW,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
        self._quality_grid = tk.Frame(inner, bg=BG_BASE)
        self._quality_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._fill_toggle_grid(self._quality_grid, self.quality_toggles,
                               QUALITY_CHIPS_ANIME if self.is_anime.get() else QUALITY_CHIPS_REAL, cols=4)

        # ── 细节质感 ─────────────────────────────────────────────
        tk.Label(inner, text="🔬 细节质感", bg=BG_BASE, fg=ACCENT_GREEN,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
        self._texture_grid = tk.Frame(inner, bg=BG_BASE)
        self._texture_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._fill_toggle_grid(self._texture_grid, self.texture_toggles,
                               TEXTURE_ANIME if self.is_anime.get() else TEXTURE_REAL, cols=4)

        # ── 色彩补充 ─────────────────────────────────────────────
        tk.Label(inner, text="🌈 色彩补充", bg=BG_BASE, fg=ACCENT_ORANGE,
                 font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
        self._color_grid = tk.Frame(inner, bg=BG_BASE)
        self._color_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._fill_toggle_grid(self._color_grid, self.color_toggles,
                               COLOR_SUPPLEMENT_ANIME if self.is_anime.get() else COLOR_SUPPLEMENT_REAL, cols=3)

        # ── 技术参数 ─────────────────────────────────────────────
        tech_row = tk.Frame(inner, bg=BG_BASE)
        tech_row.pack(fill=tk.X, padx=10, pady=(6, 4))
        tk.Label(tech_row, text="渲染引擎:", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        ttk.Combobox(tech_row, textvariable=self.render_var, values=RENDER_ENGINES,
                     state="readonly", width=18, font=("微软雅黑", 9)
                     ).pack(side=tk.LEFT, padx=(6, 16), ipady=3)
        tk.Label(tech_row, text="输出比例:", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        ttk.Combobox(tech_row, textvariable=self.ratio_var, values=OUTPUT_RATIOS,
                     state="readonly", width=10, font=("微软雅黑", 9)
                     ).pack(side=tk.LEFT, padx=(6, 0), ipady=3)
        self.render_var.trace_add("write", lambda *_: self._generate())
        self.ratio_var.trace_add("write", lambda *_: self._generate())

        # ── 负面提示词 ────────────────────────────────────────────
        neg_label_row = tk.Frame(inner, bg=BG_BASE)
        neg_label_row.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(neg_label_row, text="🚫 负面提示词", bg=BG_BASE, fg=ACCENT_RED,
                 font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
        tk.Label(neg_label_row, text="（结果显示在右侧预览）", bg=BG_BASE, fg=FG_DIM,
                 font=("微软雅黑", 8)).pack(side=tk.LEFT, padx=(6, 0))

        # 预设按钮行
        neg_preset_row = tk.Frame(inner, bg=BG_BASE)
        neg_preset_row.pack(fill=tk.X, padx=10, pady=(0, 4))
        for label, key in [("通用", "通用"), ("实拍专用", "实拍专用"), ("动画专用", "动画专用")]:
            b = tk.Button(
                neg_preset_row, text=f"+ {label}",
                bg=BG_CARD, fg=ACCENT_RED, relief=tk.FLAT,
                font=("微软雅黑", 8, "bold"), padx=10, pady=3, cursor="hand2",
                activebackground=BG_HOVER,
                command=lambda k=key: self._fill_neg_preset(k),
            )
            b.pack(side=tk.LEFT, padx=(0, 6))
            tips = {"通用": "通用负面词\n追加常用负面词（模糊/低质/水印/多余文字/解剖错误等），适合所有风格。",
                    "实拍专用": "实拍摄影负面词\n追加实拍摄影专用排除词（卡通/插画/手绘等风格偏差词）。",
                    "动画专用": "动画/二次元负面词\n追加动漫/插画专用排除词（写实质感/照片感等风格偏差词）。"}
            Tooltip(b, tips.get(key, f"追加{label}负面词预设"))

        self.neg_text = tk.Text(inner, bg=BG_CARD, fg=FG_MUTED,
                                insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
                                height=4)
        self.neg_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.neg_text.bind("<KeyRelease>", lambda _e: self._generate())

    def _refresh_detail_blocks(self):
        if self._quality_grid and self._quality_grid.winfo_exists():
            self._fill_toggle_grid(self._quality_grid, self.quality_toggles,
                                   QUALITY_CHIPS_ANIME if self.is_anime.get() else QUALITY_CHIPS_REAL, cols=4)
        if self._texture_grid and self._texture_grid.winfo_exists():
            self._fill_toggle_grid(self._texture_grid, self.texture_toggles,
                                   TEXTURE_ANIME if self.is_anime.get() else TEXTURE_REAL, cols=4)
        if self._color_grid and self._color_grid.winfo_exists():
            self._fill_toggle_grid(self._color_grid, self.color_toggles,
                                   COLOR_SUPPLEMENT_ANIME if self.is_anime.get() else COLOR_SUPPLEMENT_REAL, cols=3)

    def _fill_neg_preset(self, key):
        preset_text = NEG_PRESETS.get(key, "")
        if not preset_text:
            return
        if self.neg_text is None:
            return
        current = self.neg_text.get("1.0", tk.END).strip()
        if current:
            self.neg_text.insert(tk.END, f", {preset_text}")
        else:
            self.neg_text.insert("1.0", preset_text)
        self._generate()

    # ── Tab8：风格提炼器 ──────────────────────────────────────────
    def _build_tab_extractor(self):
        from features.camera_builder.presets import ANIME_STYLE_EXTRACTOR_PRESETS
        self._extractor_presets = ANIME_STYLE_EXTRACTOR_PRESETS

        self._extractor_detail_var = tk.StringVar(value="")
        self._extractor_btn_refs = {}   # idx → button widget，用于高亮选中

        # ── 左右可调分栏 ──────────────────────────────────────────
        h_paned = ttk.PanedWindow(self.tab_extractor, orient=tk.HORIZONTAL)
        h_paned.pack(fill=tk.BOTH, expand=True)

        # ── 左侧：预设列表（可滚动） ──────────────────────────────
        left_host = tk.Frame(h_paned, bg=BG_BASE)
        h_paned.add(left_host, weight=1)
        _, left_inner = make_scroll_canvas(left_host, bg=BG_BASE)

        tk.Label(left_inner,
                 text="点击风格预设 → 右侧查看详情，再点[应用]激活风格词块",
                 bg=BG_BASE, fg=FG_DIM, font=("微软雅黑", 8),
                 wraplength=200, justify=tk.LEFT).pack(anchor="w", padx=10, pady=(8, 4))

        categories = {}
        for i, preset in enumerate(self._extractor_presets):
            cat = preset.get("category", "其他")
            categories.setdefault(cat, []).append((i, preset))

        for cat, items in categories.items():
            cat_frame = tk.Frame(left_inner, bg=BG_BASE)
            cat_frame.pack(fill=tk.X, padx=10, pady=(6, 0))
            tk.Label(cat_frame, text=cat, bg=BG_BASE, fg=ACCENT_PURPLE,
                     font=("微软雅黑", 9, "bold")).pack(anchor="w")
            btn_row = tk.Frame(cat_frame, bg=BG_BASE)
            btn_row.pack(fill=tk.X, pady=(4, 0))
            for i, preset in items:
                b = tk.Button(
                    btn_row, text=preset["name"], bg=BG_CARD, fg=FG_PRIMARY,
                    relief=tk.FLAT, font=("微软雅黑", 8), padx=10, pady=6,
                    cursor="hand2", activebackground=BG_HOVER,
                    command=lambda idx=i: self._select_extractor_preset(idx),
                )
                b.pack(side=tk.LEFT, padx=(0, 6), pady=2)
                self._extractor_btn_refs[i] = b

        # ── 右侧：风格详情 + 操作按钮 ────────────────────────────
        right_host = tk.Frame(h_paned, bg=BG_BASE)
        h_paned.add(right_host, weight=1)

        right_top = tk.Frame(right_host, bg=BG_BASE)
        right_top.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(right_top, text="风格详情", bg=BG_BASE, fg=ACCENT_YELLOW,
                 font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
        self._extractor_match_lbl = tk.Label(right_top, text="", bg=BG_BASE,
                                              fg=ACCENT_GREEN, font=("微软雅黑", 8))
        self._extractor_match_lbl.pack(side=tk.LEFT, padx=(8, 0))

        self._extractor_detail_text = tk.Text(
            right_host, bg=BG_SURFACE, fg=FG_PRIMARY, relief=tk.FLAT,
            font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
            state=tk.DISABLED,
        )
        self._extractor_detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        # 操作按钮行
        act_row = tk.Frame(right_host, bg=BG_BASE)
        act_row.pack(fill=tk.X, padx=10, pady=(0, 6))

        self._extractor_apply_btn = tk.Button(
            act_row, text="🎭 应用风格词块", bg=ACCENT_BLUE, fg=DARK_TEXT,
            relief=tk.FLAT, font=("微软雅黑", 9, "bold"), padx=12, pady=4,
            cursor="hand2", activebackground=ACCENT_BLUE,
            state=tk.DISABLED,
            command=self._extractor_apply_style,
        )
        self._extractor_apply_btn.pack(side=tk.LEFT, padx=(0, 6))
        Tooltip(self._extractor_apply_btn,
                "🎭 应用风格词块\n将当前风格预设的关键词激活到[风格情绪]页签对应的词块上，并自动跳转到风格情绪页签。")

        tk.Button(
            act_row, text="➕ 追加到附加词", bg=ACCENT_GREEN, fg=DARK_TEXT,
            relief=tk.FLAT, font=("微软雅黑", 9, "bold"), padx=12, pady=4,
            cursor="hand2", activebackground=ACCENT_GREEN,
            command=self._extractor_append_extra,
        ).pack(side=tk.LEFT, padx=(0, 6))
        Tooltip(act_row.winfo_children()[-1],
                "➕ 追加到附加词\n将预设的所有关键词追加到右侧预览的附加词输入框，直接加入最终 Prompt 而不激活词块。")

        tk.Button(
            act_row, text="🗑 清除已选风格", bg=BG_HOVER, fg=FG_PRIMARY,
            relief=tk.FLAT, font=("微软雅黑", 8), padx=10, pady=4,
            cursor="hand2", activebackground=BG_HOVER,
            command=self._extractor_clear_style,
        ).pack(side=tk.LEFT)
        Tooltip(act_row.winfo_children()[-1],
                "🗑 清除已选风格\n取消[风格情绪]页签中所有已激活的风格/美学/情绪词块，恢复全部为未选状态。")

        # 延迟设置分割位置为 50%
        self.after(30, lambda p=h_paned: p.sash_place(0, self.tab_extractor.winfo_width() // 2, 0))

    def _select_extractor_preset(self, idx):
        self._extractor_selected_idx = idx
        preset = self._extractor_presets[idx]
        if not hasattr(self, "_extractor_detail_text") or self._extractor_detail_text is None:
            return

        # 高亮选中按钮，其余恢复
        for i, btn in self._extractor_btn_refs.items():
            btn.config(bg=ACCENT_PURPLE if i == idx else BG_CARD,
                       fg=DARK_TEXT if i == idx else FG_PRIMARY)

        zh = preset.get("zh_details", {})
        keywords = preset.get("keywords", [])
        detail_lines = [
            f"【{preset['name']}】",
            f"✦ {preset.get('zh_summary', '')}",
            "",
            f"线条风格：{zh.get('linework', preset.get('linework', ''))}",
            f"明暗处理：{zh.get('shading', preset.get('shading', ''))}",
            f"打光方式：{zh.get('lighting', preset.get('lighting', ''))}",
            f"色彩调性：{zh.get('palette', preset.get('palette', ''))}",
            f"构图风格：{zh.get('composition', preset.get('composition', ''))}",
            f"情绪基调：{zh.get('mood', preset.get('mood', ''))}",
            f"动态描述：{zh.get('motion', preset.get('motion', ''))}",
            f"背景细节：{preset.get('background_detail', '')}",
            "",
            f"注入关键词（{len(keywords)} 个）：{', '.join(keywords)}",
        ]
        self._extractor_detail_text.config(state=tk.NORMAL)
        self._extractor_detail_text.delete("1.0", tk.END)
        self._extractor_detail_text.insert("1.0", "\n".join(detail_lines))
        self._extractor_detail_text.config(state=tk.DISABLED)

        # 预计算匹配数
        match_count = sum(
            1 for kw in keywords
            for existing_kw in list(self.style_toggles) + list(self.aesthetic_toggles) + list(self.mood_toggles)
            if existing_kw.lower() in kw.lower() or kw.lower() in existing_kw.lower()
        )
        if hasattr(self, "_extractor_match_lbl"):
            if match_count:
                self._extractor_match_lbl.config(text=f"可匹配 {match_count} 个词块")
            else:
                self._extractor_match_lbl.config(text="（无匹配词块，建议用[追加到附加词]）")

        if hasattr(self, "_extractor_apply_btn"):
            self._extractor_apply_btn.config(state=tk.NORMAL)


    def _extractor_apply_style(self):
        if self._extractor_selected_idx is None:
            return
        preset = self._extractor_presets[self._extractor_selected_idx]
        keywords = preset.get("keywords", [])
        # 将关键词与现有 style/aesthetic/mood toggles 匹配并激活
        for kw in keywords:
            kw_lower = kw.lower()
            for existing_kw, bv in self.style_toggles.items():
                if existing_kw.lower() in kw_lower or kw_lower in existing_kw.lower():
                    bv.set(True)
            for existing_kw, bv in self.aesthetic_toggles.items():
                if existing_kw.lower() in kw_lower or kw_lower in existing_kw.lower():
                    bv.set(True)
            for existing_kw, bv in self.mood_toggles.items():
                if existing_kw.lower() in kw_lower or kw_lower in existing_kw.lower():
                    bv.set(True)
        # 刷新风格格子按钮颜色（_fill_toggle_grid 现在会读取保存的 BoolVar 状态）
        self._refresh_style_toggle_colors()
        self._generate()
        # 跳转到风格情绪页签
        if self.nb and self.tab_style:
            try:
                self.nb.select(self.tab_style)
            except Exception:
                pass

    def _extractor_clear_style(self):
        """清除所有风格/美学/情绪词块的选中状态"""
        for bv in self.style_toggles.values():
            bv.set(False)
        for bv in self.aesthetic_toggles.values():
            bv.set(False)
        for bv in self.mood_toggles.values():
            bv.set(False)
        self._refresh_style_toggle_colors()
        self._generate()


    def _refresh_style_toggle_colors(self):
        """重新渲染风格/美学/情绪格子以反映当前 BooleanVar 状态"""
        if self._style_grid and self._style_grid.winfo_exists():
            self._fill_toggle_grid(self._style_grid, self.style_toggles,
                                   STYLE_ANIME if self.is_anime.get() else STYLE_REAL, cols=4)
        if self._aesthetic_grid and self._aesthetic_grid.winfo_exists():
            self._fill_toggle_grid(self._aesthetic_grid, self.aesthetic_toggles,
                                   AESTHETIC_ANIME if self.is_anime.get() else AESTHETIC_REAL, cols=4)
        if self._mood_grid and self._mood_grid.winfo_exists():
            self._fill_toggle_grid(self._mood_grid, self.mood_toggles,
                                   MOOD_ANIME if self.is_anime.get() else MOOD_REAL, cols=4)

    def _extractor_append_extra(self):
        if self._extractor_selected_idx is None:
            return
        preset = self._extractor_presets[self._extractor_selected_idx]
        keywords = preset.get("keywords", [])
        if not keywords:
            return
        kw_str = ", ".join(keywords)
        current = self.extra_var.get().strip()
        self.extra_var.set((current + ", " + kw_str) if current else kw_str)
        self._generate()

    # ── 模式切换 ────────────────────────────────────────────────
    def _toggle_mode(self):
        self.is_anime.set(not self.is_anime.get())
        on = self.is_anime.get()
        self._mode_btn.config(
            text="● 开" if on else "○ 关",
            bg=ACCENT_PURPLE if on else BG_HOVER,
            fg=DARK_TEXT if on else FG_PRIMARY,
        )
        self._render_params()
        self._refresh_subject_chips()
        self._refresh_style_blocks()
        self._refresh_detail_blocks()
        self._generate()

    # ── 右侧预览面板 ─────────────────────────────────────────────
    def _build_preview_panel(self, parent):
        parent.configure(bg="#181825")

        extra_row = tk.Frame(parent, bg="#181825")
        extra_row.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(extra_row, text="附加词:", bg="#181825", fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(side=tk.LEFT)
        extra_entry = tk.Entry(extra_row, textvariable=self.extra_var, bg=BG_CARD, fg=FG_PRIMARY,
                               insertbackground=FG_PRIMARY, relief=tk.FLAT, font=("微软雅黑", 9))
        extra_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(8, 0))
        extra_entry.bind("<KeyRelease>", lambda _e: self._generate())

        # ── 外层：左右水平分栏 ──────────────────────────────────────
        h_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        h_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 8))

        # ── 左列：垂直分栏 → 正面(英文) / 负面(英文) ─────────────────
        en_col = tk.Frame(h_paned, bg="#181825")
        h_paned.add(en_col, weight=3)

        en_v_paned = ttk.PanedWindow(en_col, orient=tk.VERTICAL)
        en_v_paned.pack(fill=tk.BOTH, expand=True)

        # 正面英文
        en_pos_outer = tk.Frame(en_v_paned, bg="#181825")
        en_v_paned.add(en_pos_outer, weight=3)
        en_pos_hdr = tk.Frame(en_pos_outer, bg="#181825")
        en_pos_hdr.pack(fill=tk.X, pady=(4, 2))
        tk.Label(en_pos_hdr, text="🔤 正面提示词", bg="#181825", fg=ACCENT_GREEN,
                 font=("微软雅黑", 8, "bold")).pack(side=tk.LEFT, padx=6)
        en_pos_frame = tk.Frame(en_pos_outer, bg=BG_SURFACE)
        en_pos_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_text = tk.Text(en_pos_frame, bg=BG_SURFACE, fg=ACCENT_GREEN,
                                    relief=tk.FLAT, font=("微软雅黑", 9),
                                    wrap=tk.WORD, padx=8, pady=6, state=tk.DISABLED)
        en_pos_sb = ttk.Scrollbar(en_pos_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=en_pos_sb.set)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        en_pos_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # 负面英文
        en_neg_outer = tk.Frame(en_v_paned, bg="#181825")
        en_v_paned.add(en_neg_outer, weight=2)
        en_neg_hdr = tk.Frame(en_neg_outer, bg="#181825")
        en_neg_hdr.pack(fill=tk.X, pady=(6, 2))
        tk.Label(en_neg_hdr, text="🚫 负面提示词", bg="#181825", fg=ACCENT_RED,
                 font=("微软雅黑", 8, "bold")).pack(side=tk.LEFT, padx=6)

        def _copy_neg():
            import pyperclip
            txt = self.neg_preview_text.get("1.0", tk.END).strip() if self.neg_preview_text else ""
            if txt:
                pyperclip.copy(txt)
                _copy_neg_btn.config(text="✓ 已复制")
                self.after(1500, lambda: _copy_neg_btn.config(text="📋 复制负面词"))

        def _toggle_neg_positive():
            self.neg_to_positive_enabled.set(not self.neg_to_positive_enabled.get())
            on = self.neg_to_positive_enabled.get()
            self._neg_btn_ref.config(
                text="● 已转正面排除词" if on else "○ 转为正面排除词",
                bg=ACCENT_ORANGE if on else BG_HOVER,
                fg=DARK_TEXT if on else FG_PRIMARY,
            )
            self._generate()

        _copy_neg_btn = tk.Button(
            en_neg_hdr, text="📋 复制负面词", command=_copy_neg,
            bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
            font=("微软雅黑", 8), padx=8, pady=1, cursor="hand2",
            activebackground=BG_HOVER,
        )
        _copy_neg_btn.pack(side=tk.RIGHT, padx=(0, 6))

        _neg_btn = tk.Button(
            en_neg_hdr, text="○ 转为正面排除词", command=_toggle_neg_positive,
            bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
            font=("微软雅黑", 8, "bold"), padx=8, pady=1, cursor="hand2",
            activebackground=BG_HOVER,
        )
        _neg_btn.pack(side=tk.RIGHT, padx=(0, 4))
        self._neg_btn_ref = _neg_btn

        en_neg_frame = tk.Frame(en_neg_outer, bg=BG_SURFACE)
        en_neg_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        self.neg_preview_text = tk.Text(
            en_neg_frame, bg=BG_SURFACE, fg=ACCENT_RED,
            relief=tk.FLAT, font=("微软雅黑", 9),
            wrap=tk.WORD, padx=8, pady=4, state=tk.DISABLED,
        )
        en_neg_sb = ttk.Scrollbar(en_neg_frame, orient="vertical", command=self.neg_preview_text.yview)
        self.neg_preview_text.configure(yscrollcommand=en_neg_sb.set)
        self.neg_preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
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
                 font=("微软雅黑", 8, "bold")).pack(anchor="w", padx=6, pady=(4, 2))
        zh_pos_frame = tk.Frame(zh_pos_outer, bg=BG_BASE)
        zh_pos_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_zh_text = tk.Text(zh_pos_frame, bg=BG_BASE, fg=ACCENT_YELLOW,
                                       relief=tk.FLAT, font=("微软雅黑", 9),
                                       wrap=tk.WORD, padx=8, pady=6, state=tk.DISABLED)
        zh_pos_sb = ttk.Scrollbar(zh_pos_frame, orient="vertical", command=self.preview_zh_text.yview)
        self.preview_zh_text.configure(yscrollcommand=zh_pos_sb.set)
        self.preview_zh_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        zh_pos_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # 负面中文
        zh_neg_outer = tk.Frame(zh_v_paned, bg=BG_BASE)
        zh_v_paned.add(zh_neg_outer, weight=2)
        tk.Label(zh_neg_outer, text="🀄 负面中文对照", bg=BG_BASE, fg=ACCENT_RED,
                 font=("微软雅黑", 8, "bold")).pack(anchor="w", padx=6, pady=(6, 2))
        zh_neg_frame = tk.Frame(zh_neg_outer, bg=BG_BASE)
        zh_neg_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        self.neg_zh_preview_text = tk.Text(
            zh_neg_frame, bg=BG_BASE, fg=ACCENT_RED,
            relief=tk.FLAT, font=("微软雅黑", 9),
            wrap=tk.WORD, padx=8, pady=4, state=tk.DISABLED,
        )
        zh_neg_sb = ttk.Scrollbar(zh_neg_frame, orient="vertical", command=self.neg_zh_preview_text.yview)
        self.neg_zh_preview_text.configure(yscrollcommand=zh_neg_sb.set)
        self.neg_zh_preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        zh_neg_sb.pack(side=tk.RIGHT, fill=tk.Y)

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
    def _build_prompt(self):
        subject = ""
        if self.subject_text:
            subj = self.subject_text.get("1.0", tk.END).strip()
            if subj and subj != self._SUBJECT_HINT:
                subject = subj

        environment = ""
        if self.environ_text:
            env = self.environ_text.get("1.0", tk.END).strip()
            if env and env != self._ENVIRON_HINT:
                environment = env

        parameters = []
        params = PARAMS_ANIME if self.is_anime.get() else PARAMS_REAL
        for name, (_, kw_fn) in params.items():
            if not self.param_checks.get(name, tk.BooleanVar(value=False)).get():
                continue
            custom_val = self.custom_vars.get(name, tk.StringVar()).get().strip()
            if custom_val and custom_val != "自定义...":
                kw = custom_val
            else:
                selected_val = self.param_vars.get(name, tk.StringVar()).get()
                kw = kw_fn(selected_val)
            if kw:
                parameters.append(kw)

        camera_terms = []
        if self.shot_enabled.get():
            camera_terms.append(SHOT_SCALE[self.shot_var.get()][0])
        if self.elevation_enabled.get():
            camera_terms.append(CAMERA_ELEVATION[self.elevation_var.get()][0])
        if self.subject_angle_enabled.get():
            camera_terms.append(SUBJECT_ANGLE[self.subject_angle_var.get()][0])
        if self.light_dir_enabled.get():
            kw = self._light_keyword()
            if kw:
                camera_terms.append(kw)
        if self.rim_light_var.get():
            camera_terms.append("rim light")

        filters = []
        for english_keyword, bv in self.filter_toggles.items():
            if bv.get():
                filters.append(english_keyword)

        style_terms = []
        for kw, bv in self.style_toggles.items():
            if bv.get():
                style_terms.append(kw)
        for kw, bv in self.aesthetic_toggles.items():
            if bv.get():
                style_terms.append(kw)
        for kw, bv in self.mood_toggles.items():
            if bv.get():
                style_terms.append(kw)
        motion = self.motion_var.get().strip()
        if motion and motion != "（不指定）":
            style_terms.append(motion)

        detail_terms = []
        for kw, bv in self.quality_toggles.items():
            if bv.get():
                detail_terms.append(kw)
        for kw, bv in self.texture_toggles.items():
            if bv.get():
                detail_terms.append(kw)
        for kw, bv in self.color_toggles.items():
            if bv.get():
                detail_terms.append(kw)
        render = self.render_var.get().strip()
        ratio = self.ratio_var.get().strip()
        extra = self.extra_var.get().strip()
        return build_camera_prompt(CameraPromptSpec(
            subject=subject,
            environment=environment,
            parameters=parameters,
            camera_terms=camera_terms,
            filters=filters,
            style_terms=style_terms,
            detail_terms=detail_terms,
            render=render,
            ratio=ratio,
            extra=extra,
        ))

    def _build_prompt_zh(self):
        mode = "二次元" if self.is_anime.get() else "实拍"

        # ── 主体场景 ────────────────────────────────────────────────
        subject_zh = self._build_subject_scene_zh()

        # ── 基础参数 ────────────────────────────────────────────────
        param_lines = []
        params = PARAMS_ANIME if self.is_anime.get() else PARAMS_REAL
        for name, (_, kw_fn) in params.items():
            if not self.param_checks.get(name, tk.BooleanVar(value=False)).get():
                continue
            custom_val = self.custom_vars.get(name, tk.StringVar()).get().strip()
            if custom_val and custom_val != "自定义...":
                kw = custom_val
            else:
                selected_val = self.param_vars.get(name, tk.StringVar()).get()
                kw = kw_fn(selected_val)
            if kw:
                label = ZH_PARAM_NAMES.get(name, name)
                param_lines.append(f"【{label}】{kw_to_zh(kw)}")

        # ── 镜头参数 ────────────────────────────────────────────────
        camera_lines = []
        if self.shot_enabled.get():
            kw, desc = SHOT_SCALE[self.shot_var.get()]
            camera_lines.append(f"【景别】{desc.split('—')[0].strip()}")
        if self.elevation_enabled.get():
            kw, desc = CAMERA_ELEVATION[self.elevation_var.get()]
            camera_lines.append(f"【俯仰角】{desc.split('—')[0].strip()}")
        if self.subject_angle_enabled.get():
            kw, desc = SUBJECT_ANGLE[self.subject_angle_var.get()]
            camera_lines.append(f"【方位角】{desc.split('—')[0].strip()}")
        if self.light_dir_enabled.get():
            kw = self._light_keyword()
            if kw:
                camera_lines.append(f"【主光源】{kw_to_zh(kw)}")
        if self.rim_light_var.get():
            camera_lines.append("【轮廓光】已启用")

        # ── 滤镜积木 ────────────────────────────────────────────────
        active_filters = []
        for english_keyword, bv in self.filter_toggles.items():
            if bv.get():
                zh = kw_to_zh(english_keyword)
                active_filters.append(zh)

        # ── 风格情绪 ────────────────────────────────────────────────
        style_zh = self._build_style_mood_zh()

        # ── 细节技术 ────────────────────────────────────────────────
        detail_zh = self._build_detail_tech_zh()

        # ── 附加词 ──────────────────────────────────────────────────
        extra = self.extra_var.get().strip()
        return build_prompt_zh_text(
            mode=mode,
            subject_scene=subject_zh,
            params=param_lines,
            camera=camera_lines,
            filters=active_filters,
            style_mood=style_zh,
            detail_tech=detail_zh,
            extra=extra,
        )

    def _build_subject_scene_zh(self):
        subject = ""
        environment = ""
        if self.subject_text:
            subj = self.subject_text.get("1.0", tk.END).strip()
            if subj and subj != self._SUBJECT_HINT:
                subject = subj
        if self.environ_text:
            env = self.environ_text.get("1.0", tk.END).strip()
            if env and env != self._ENVIRON_HINT:
                environment = env
        return build_subject_scene_zh(subject, environment)

    def _build_style_mood_zh(self):
        from features.camera_builder.presets import (
            STYLE_REAL, STYLE_ANIME,
            AESTHETIC_REAL, AESTHETIC_ANIME,
            MOOD_REAL, MOOD_ANIME,
        )
        is_anime = self.is_anime.get()
        style_zh_map = {kw: zh for kw, zh in (STYLE_ANIME if is_anime else STYLE_REAL)}
        aesthetic_zh_map = {kw: zh for kw, zh in (AESTHETIC_ANIME if is_anime else AESTHETIC_REAL)}
        mood_zh_map = {kw: zh for kw, zh in (MOOD_ANIME if is_anime else MOOD_REAL)}

        return build_style_mood_zh_text(
            styles=[kw for kw, bv in self.style_toggles.items() if bv.get()],
            aesthetics=[kw for kw, bv in self.aesthetic_toggles.items() if bv.get()],
            moods=[kw for kw, bv in self.mood_toggles.items() if bv.get()],
            motion=self.motion_var.get().strip(),
            style_map=style_zh_map,
            aesthetic_map=aesthetic_zh_map,
            mood_map=mood_zh_map,
            fallback=kw_to_zh,
        )

    def _build_detail_tech_zh(self):
        from features.camera_builder.presets import (
            QUALITY_CHIPS_REAL, QUALITY_CHIPS_ANIME,
            TEXTURE_REAL, TEXTURE_ANIME,
            COLOR_SUPPLEMENT_REAL, COLOR_SUPPLEMENT_ANIME,
        )
        is_anime = self.is_anime.get()
        quality_zh_map = {kw: zh for kw, zh in (QUALITY_CHIPS_ANIME if is_anime else QUALITY_CHIPS_REAL)}
        texture_zh_map = {kw: zh for kw, zh in (TEXTURE_ANIME if is_anime else TEXTURE_REAL)}
        color_zh_map = {kw: zh for kw, zh in (COLOR_SUPPLEMENT_ANIME if is_anime else COLOR_SUPPLEMENT_REAL)}
        return build_detail_tech_zh_text(
            qualities=[kw for kw, bv in self.quality_toggles.items() if bv.get()],
            textures=[kw for kw, bv in self.texture_toggles.items() if bv.get()],
            colors=[kw for kw, bv in self.color_toggles.items() if bv.get()],
            render=self.render_var.get().strip(),
            ratio=self.ratio_var.get().strip(),
            quality_map=quality_zh_map,
            texture_map=texture_zh_map,
            color_map=color_zh_map,
        )

    def _build_negative_zh(self, neg_text: str) -> str:
        return build_negative_zh_text(neg_text, NEGATIVE_ZH_MAP, kw_to_zh)

    def _generate(self):
        base_prompt = self._build_prompt()
        # 如果"转为正面排除词"开关打开，在正面 prompt 后追加排除段
        if self.neg_to_positive_enabled.get() and self.neg_text is not None:
            neg = self.neg_text.get("1.0", tk.END).strip()
            if neg:
                base_prompt = append_negative_as_positive(base_prompt, neg)

        if self.preview_text is None:
            return
        neg = self.neg_text.get("1.0", tk.END).strip() if self.neg_text is not None else ""
        PreviewPanel.render(
            preview_text=self.preview_text,
            preview_zh_text=self.preview_zh_text,
            neg_preview_text=self.neg_preview_text,
            neg_zh_preview_text=self.neg_zh_preview_text,
            prompt=base_prompt,
            prompt_zh=self._build_prompt_zh(),
            negative_text=neg,
            negative_zh=self._build_negative_zh(neg) if neg else "",
        )

    def _copy(self):
        import pyperclip
        pyperclip.copy(self._build_prompt())
        self.title("提示词生成器  ✓ 已复制")
        self.after(2000, lambda: self.title("提示词生成器"))

    def _insert(self):
        prompt = self._build_prompt()
        title = tkinter.simpledialog.askstring(
            "保存为 Prompt", "请输入标题：",
            parent=self, initialvalue="📷 摄影机设置",
        )
        if title is None:
            return
        self.on_insert(title.strip() or "📷 摄影机设置", prompt)
        self.destroy()
