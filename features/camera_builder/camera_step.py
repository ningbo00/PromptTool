import tkinter as tk
from tkinter import ttk

from shared.ui_kit import (
    make_scroll_canvas, BG_BASE, BG_SURFACE, BG_CARD, BG_HOVER,
    FG_PRIMARY, FG_MUTED, FG_DIM, ACCENT_BLUE, ACCENT_GREEN,
    ACCENT_PURPLE, ACCENT_YELLOW, ACCENT_CYAN, DARK_TEXT,
)
from features.camera_builder.presets import PARAMS_REAL, PARAMS_ANIME


def create_camera_step(notebook, builder):
    step = tk.Frame(notebook, bg=BG_BASE)
    notebook.add(step, text="3 镜头")
    inner = ttk.Notebook(step, style="Dark.TNotebook")
    inner.pack(fill=tk.BOTH, expand=True)

    builder.tab_params = tk.Frame(inner, bg=BG_BASE)
    builder.tab_camera = tk.Frame(inner, bg=BG_SURFACE)
    inner.add(builder.tab_params, text="基础参数")
    inner.add(builder.tab_camera, text="镜头位置")
    return step


def build_params_tab(builder):
    builder._params_scroll_host = builder.tab_params
    render_params(builder)

def render_params(builder):
    for w in builder._params_scroll_host.winfo_children():
        w.destroy()
    builder.param_vars.clear()
    builder.custom_vars.clear()
    builder.param_checks.clear()

    params = PARAMS_ANIME if builder.is_anime.get() else PARAMS_REAL
    _, inner = make_scroll_canvas(builder._params_scroll_host, bg=BG_BASE)

    for name, (options, _) in params.items():
        row = tk.Frame(inner, bg=BG_SURFACE, pady=5)
        row.pack(fill=tk.X, pady=2, padx=4)

        enabled = tk.BooleanVar(value=True)
        builder.param_checks[name] = enabled
        tk.Checkbutton(row, variable=enabled, bg=BG_SURFACE, activebackground=BG_SURFACE,
                       selectcolor=BG_HOVER, fg=FG_PRIMARY,
                       command=builder._generate).pack(side=tk.LEFT, padx=(6, 0))

        tk.Label(row, text=name, bg=BG_SURFACE, fg=FG_PRIMARY,
                 font=("微软雅黑", 9, "bold"), width=10, anchor="w").pack(side=tk.LEFT, padx=(4, 8))

        selected_sv = tk.StringVar(value=options[0])
        builder.param_vars[name] = selected_sv
        cb = ttk.Combobox(row, textvariable=selected_sv, values=options,
                          state="readonly", width=28, font=("微软雅黑", 9))
        cb.pack(side=tk.LEFT, padx=(0, 8))
        cb.bind("<<ComboboxSelected>>", lambda _e: builder._generate())

        custom_sv = tk.StringVar()
        builder.custom_vars[name] = custom_sv
        entry = tk.Entry(row, textvariable=custom_sv, bg=BG_CARD, fg=FG_PRIMARY,
                         insertbackground=FG_PRIMARY, relief=tk.FLAT,
                         font=("微软雅黑", 9), width=20)
        entry.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        entry.insert(0, "自定义...")
        entry.config(fg=FG_DIM)
        entry.bind("<FocusIn>",  lambda _e, ent=entry: builder._entry_focus_in(ent))
        entry.bind("<FocusOut>", lambda _e, ent=entry: builder._entry_focus_out(ent))
        entry.bind("<KeyRelease>", lambda _e: builder._generate())

def build_camera_tab(builder):
    _, inner = make_scroll_canvas(builder.tab_camera, bg=BG_SURFACE)
    build_sliders_section(builder, inner)

def build_sliders_section(builder, parent):
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
                       command=builder._generate).pack(side=tk.RIGHT)

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
        setattr(builder, result_label_attr, lbl)
        ttk.Separator(outer, orient="horizontal").pack(fill=tk.X, padx=16, pady=6)

    _slider_section(
        "🔭 景别 Shot Scale", builder.shot_var, builder.shot_enabled,
        ["超远景", "远景", "中景", "近景", "特写", "微距", "超微距"], 0, 6,
        ACCENT_PURPLE, builder._on_shot_change, "shot_result_label",
    )
    _slider_section(
        "📐 俯仰角 Camera Elevation", builder.elevation_var, builder.elevation_enabled,
        ["极端仰", "仰拍", "轻仰", "平视", "轻俯", "俯拍", "顶视"], 0, 6,
        ACCENT_YELLOW, builder._on_elevation_change, "elevation_result_label",
    )
    _slider_section(
        "🧭 主体方位角 Subject Angle", builder.subject_angle_var, builder.subject_angle_enabled,
        ["正面", "左前", "左侧", "左后", "背面", "右后", "右侧", "右前"], 0, 7,
        ACCENT_CYAN, builder._on_angle_change, "angle_result_label",
    )

    builder._on_shot_change()
    builder._on_elevation_change()
    builder._on_angle_change()

    # ── 主光源 ──
    sec3 = tk.Frame(outer, bg=BG_SURFACE)
    sec3.pack(fill=tk.X, padx=16, pady=(0, 6))
    hdr3 = tk.Frame(sec3, bg=BG_SURFACE)
    hdr3.pack(fill=tk.X)
    tk.Label(hdr3, text="💡 主光源 Key Light", bg=BG_SURFACE, fg=FG_PRIMARY,
             font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
    tk.Checkbutton(hdr3, text="加入生成结果", variable=builder.light_dir_enabled,
                   bg=BG_SURFACE, fg=FG_MUTED, activebackground=BG_SURFACE,
                   selectcolor=BG_HOVER, font=("微软雅黑", 8),
                   command=builder._generate).pack(side=tk.RIGHT)

    light_body = tk.Frame(sec3, bg=BG_SURFACE)
    light_body.pack(fill=tk.X, pady=(8, 0))

    SPHERE_SIZE = 160
    builder._light_sphere_canvas = tk.Canvas(
        light_body, width=SPHERE_SIZE, height=SPHERE_SIZE,
        bg="#1a1a2e", highlightthickness=1, highlightbackground=BG_HOVER,
        cursor="crosshair",
    )
    builder._light_sphere_canvas.pack(side=tk.LEFT, padx=(0, 12))
    builder._draw_light_sphere()
    builder._light_sphere_canvas.bind("<Button-1>",        builder._sphere_click)
    builder._light_sphere_canvas.bind("<B1-Motion>",       builder._sphere_drag)
    builder._light_sphere_canvas.bind("<ButtonRelease-1>", builder._sphere_release)

    right_col = tk.Frame(light_body, bg=BG_SURFACE)
    right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    hemi_row = tk.Frame(right_col, bg=BG_SURFACE)
    hemi_row.pack(fill=tk.X, pady=(0, 6))
    tk.Label(hemi_row, text="视角面:", bg=BG_SURFACE, fg=FG_MUTED,
             font=("微软雅黑", 8)).pack(side=tk.LEFT)
    builder._hemi_front_btn = tk.Button(
        hemi_row, text="前", bg=ACCENT_BLUE, fg=DARK_TEXT,
        relief=tk.FLAT, font=("微软雅黑", 8, "bold"), padx=8, pady=2,
        cursor="hand2", activebackground=ACCENT_BLUE,
        command=lambda: builder._set_hemi(False),
    )
    builder._hemi_front_btn.pack(side=tk.LEFT, padx=(6, 2))
    builder._hemi_back_btn = tk.Button(
        hemi_row, text="后", bg=BG_HOVER, fg=FG_PRIMARY,
        relief=tk.FLAT, font=("微软雅黑", 8, "bold"), padx=8, pady=2,
        cursor="hand2", activebackground=BG_HOVER,
        command=lambda: builder._set_hemi(True),
    )
    builder._hemi_back_btn.pack(side=tk.LEFT)

    color_row = tk.Frame(right_col, bg=BG_SURFACE)
    color_row.pack(fill=tk.X, pady=(0, 6))
    tk.Label(color_row, text="光源颜色", bg=BG_SURFACE, fg=FG_MUTED,
             font=("微软雅黑", 8)).pack(side=tk.LEFT)
    builder._light_color_btn = tk.Button(
        color_row, text="", width=3, relief=tk.FLAT, cursor="hand2",
        bg=builder.light_color, activebackground=builder.light_color,
        command=builder._pick_light_color,
    )
    builder._light_color_btn.pack(side=tk.LEFT, padx=(8, 0), ipady=6)
    builder._light_color_label = tk.Label(
        color_row, text=builder.light_color, bg=BG_SURFACE, fg=FG_MUTED,
        font=("微软雅黑", 8),
    )
    builder._light_color_label.pack(side=tk.LEFT, padx=(6, 0))

    builder._azimuth_label = tk.Label(right_col, text="", bg=BG_SURFACE,
                                   fg=ACCENT_YELLOW, font=("微软雅黑", 8))
    builder._azimuth_label.pack(anchor="w", pady=(0, 2))
    builder._elev_label = tk.Label(right_col, text="", bg=BG_SURFACE,
                                fg=ACCENT_YELLOW, font=("微软雅黑", 8))
    builder._elev_label.pack(anchor="w", pady=(0, 2))
    builder._light_kw_label = tk.Label(right_col, text="", bg=BG_SURFACE,
                                    fg=ACCENT_GREEN, font=("微软雅黑", 8),
                                    wraplength=160, justify=tk.LEFT)
    builder._light_kw_label.pack(anchor="w")
    builder._update_light_labels()

    ttk.Separator(outer, orient="horizontal").pack(fill=tk.X, padx=16, pady=6)

    # ── 轮廓光 ──
    sec4 = tk.Frame(outer, bg=BG_SURFACE)
    sec4.pack(fill=tk.X, padx=16, pady=(0, 12))
    tk.Label(sec4, text="✨ 轮廓光 Rim Light", bg=BG_SURFACE, fg=FG_PRIMARY,
             font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
    builder._rim_btn = tk.Button(
        sec4, text="○ 关", bg=BG_HOVER, fg=FG_PRIMARY,
        relief=tk.FLAT, font=("微软雅黑", 9, "bold"), padx=10, pady=2,
        cursor="hand2", command=builder._toggle_rim_light,
    )
    builder._rim_btn.pack(side=tk.RIGHT)
