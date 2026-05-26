"""
摄影机参数构建器窗口（从 main.py 抽取，依赖 shared/ 和 presets.py）
"""
import math
import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog
from tkinter.colorchooser import askcolor

from shared.ui_kit import (
    apply_dark_notebook_style, Tooltip,
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
from features.camera_builder.scene_step import create_scene_step, build_subject_tab, fill_chips
from features.camera_builder.style_step import (
    create_style_step, build_preset_tab, build_style_tab, build_filter_tab,
    build_extractor_tab, fill_toggle_grid,
)
from features.camera_builder.camera_step import (
    create_camera_step, build_params_tab, build_camera_tab, render_params,
)
from features.camera_builder.output_step import create_output_step, build_detail_tab
from features.camera_builder.preview_panel import PreviewPanel
from features.camera_builder.presets import (
    PARAMS_REAL, PARAMS_ANIME,
    SHOT_SCALE, CAMERA_ELEVATION, SUBJECT_ANGLE,
    PRESETS_REAL, PRESETS_ANIME,
    SUBJECT_CHIPS_REAL, SUBJECT_CHIPS_ANIME,
    ENVIRONMENT_CHIPS_REAL, ENVIRONMENT_CHIPS_ANIME,
    STYLE_REAL, STYLE_ANIME,
    MOOD_REAL, MOOD_ANIME,
    TEXTURE_REAL, TEXTURE_ANIME,
    COLOR_SUPPLEMENT_REAL, COLOR_SUPPLEMENT_ANIME,
    WEATHER_CHIPS_REAL, WEATHER_CHIPS_ANIME,
    SUBJECT_COUNT_REAL, SUBJECT_COUNT_ANIME,
    AESTHETIC_REAL, AESTHETIC_ANIME,
    QUALITY_CHIPS_REAL, QUALITY_CHIPS_ANIME,
    NEG_PRESETS,
    NEGATIVE_ZH_MAP,
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




    # ── Tab4：预设 ────────────────────────────────────────────────


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

    def _refresh_subject_chips(self):
        if self._subject_chips_frame and self._subject_chips_frame.winfo_exists():
            fill_chips(self, self._subject_chips_frame, self.subject_text,
                             SUBJECT_CHIPS_ANIME if self.is_anime.get() else SUBJECT_CHIPS_REAL)
        if self._count_chips_frame and self._count_chips_frame.winfo_exists():
            fill_chips(self, self._count_chips_frame, self.subject_text,
                             SUBJECT_COUNT_ANIME if self.is_anime.get() else SUBJECT_COUNT_REAL)
        if self._environ_chips_frame and self._environ_chips_frame.winfo_exists():
            fill_chips(self, self._environ_chips_frame, self.environ_text,
                             ENVIRONMENT_CHIPS_ANIME if self.is_anime.get() else ENVIRONMENT_CHIPS_REAL)
        if self._weather_chips_frame and self._weather_chips_frame.winfo_exists():
            fill_chips(self, self._weather_chips_frame, self.environ_text,
                             WEATHER_CHIPS_ANIME if self.is_anime.get() else WEATHER_CHIPS_REAL)

    # ── Tab6：风格情绪 ────────────────────────────────────────────


    def _refresh_style_blocks(self):
        if self._style_grid and self._style_grid.winfo_exists():
            fill_toggle_grid(self, self._style_grid, self.style_toggles,
                                   STYLE_ANIME if self.is_anime.get() else STYLE_REAL, cols=4)
        if self._aesthetic_grid and self._aesthetic_grid.winfo_exists():
            fill_toggle_grid(self, self._aesthetic_grid, self.aesthetic_toggles,
                                   AESTHETIC_ANIME if self.is_anime.get() else AESTHETIC_REAL, cols=4)
        if self._mood_grid and self._mood_grid.winfo_exists():
            fill_toggle_grid(self, self._mood_grid, self.mood_toggles,
                                   MOOD_ANIME if self.is_anime.get() else MOOD_REAL, cols=4)

    # ── Tab7：细节技术 ────────────────────────────────────────────

    def _refresh_detail_blocks(self):
        if self._quality_grid and self._quality_grid.winfo_exists():
            fill_toggle_grid(self, self._quality_grid, self.quality_toggles,
                                   QUALITY_CHIPS_ANIME if self.is_anime.get() else QUALITY_CHIPS_REAL, cols=4)
        if self._texture_grid and self._texture_grid.winfo_exists():
            fill_toggle_grid(self, self._texture_grid, self.texture_toggles,
                                   TEXTURE_ANIME if self.is_anime.get() else TEXTURE_REAL, cols=4)
        if self._color_grid and self._color_grid.winfo_exists():
            fill_toggle_grid(self, self._color_grid, self.color_toggles,
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
            fill_toggle_grid(self, self._style_grid, self.style_toggles,
                                   STYLE_ANIME if self.is_anime.get() else STYLE_REAL, cols=4)
        if self._aesthetic_grid and self._aesthetic_grid.winfo_exists():
            fill_toggle_grid(self, self._aesthetic_grid, self.aesthetic_toggles,
                                   AESTHETIC_ANIME if self.is_anime.get() else AESTHETIC_REAL, cols=4)
        if self._mood_grid and self._mood_grid.winfo_exists():
            fill_toggle_grid(self, self._mood_grid, self.mood_toggles,
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
        render_params(self)
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
