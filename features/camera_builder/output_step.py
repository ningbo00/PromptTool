import tkinter as tk
from tkinter import ttk

from shared.ui_kit import (
    make_scroll_canvas, Tooltip, BG_BASE, BG_CARD, BG_HOVER,
    FG_PRIMARY, FG_MUTED, FG_DIM, ACCENT_GREEN, ACCENT_YELLOW,
    ACCENT_RED, ACCENT_ORANGE,
)
from features.camera_builder.presets import (
    TEXTURE_REAL, TEXTURE_ANIME, COLOR_SUPPLEMENT_REAL, COLOR_SUPPLEMENT_ANIME,
    RENDER_ENGINES, OUTPUT_RATIOS, QUALITY_CHIPS_REAL, QUALITY_CHIPS_ANIME,
)
from features.camera_builder.negative_panel import fill_negative_preset
from features.camera_builder.style_step import fill_toggle_grid


def create_output_step(notebook, builder):
    step = tk.Frame(notebook, bg=BG_BASE)
    notebook.add(step, text="4 输出")
    builder.tab_detail = tk.Frame(step, bg=BG_BASE)
    builder.tab_detail.pack(fill=tk.BOTH, expand=True)
    return step


def build_detail_tab(builder):
    _, inner = make_scroll_canvas(builder.tab_detail, bg=BG_BASE)

    # ── 质量词块 ─────────────────────────────────────────────
    tk.Label(inner, text="⭐ 质量词块", bg=BG_BASE, fg=ACCENT_YELLOW,
             font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
    builder._quality_grid = tk.Frame(inner, bg=BG_BASE)
    builder._quality_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
    fill_toggle_grid(builder, builder._quality_grid, builder.quality_toggles,
                           QUALITY_CHIPS_ANIME if builder.is_anime.get() else QUALITY_CHIPS_REAL, cols=4)

    # ── 细节质感 ─────────────────────────────────────────────
    tk.Label(inner, text="🔬 细节质感", bg=BG_BASE, fg=ACCENT_GREEN,
             font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
    builder._texture_grid = tk.Frame(inner, bg=BG_BASE)
    builder._texture_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
    fill_toggle_grid(builder, builder._texture_grid, builder.texture_toggles,
                           TEXTURE_ANIME if builder.is_anime.get() else TEXTURE_REAL, cols=4)

    # ── 色彩补充 ─────────────────────────────────────────────
    tk.Label(inner, text="🌈 色彩补充", bg=BG_BASE, fg=ACCENT_ORANGE,
             font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
    builder._color_grid = tk.Frame(inner, bg=BG_BASE)
    builder._color_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
    fill_toggle_grid(builder, builder._color_grid, builder.color_toggles,
                           COLOR_SUPPLEMENT_ANIME if builder.is_anime.get() else COLOR_SUPPLEMENT_REAL, cols=3)

    # ── 技术参数 ─────────────────────────────────────────────
    tech_row = tk.Frame(inner, bg=BG_BASE)
    tech_row.pack(fill=tk.X, padx=10, pady=(6, 4))
    tk.Label(tech_row, text="渲染引擎:", bg=BG_BASE, fg=FG_MUTED,
             font=("微软雅黑", 9)).pack(side=tk.LEFT)
    ttk.Combobox(tech_row, textvariable=builder.render_var, values=RENDER_ENGINES,
                 state="readonly", width=18, font=("微软雅黑", 9)
                 ).pack(side=tk.LEFT, padx=(6, 16), ipady=3)
    tk.Label(tech_row, text="输出比例:", bg=BG_BASE, fg=FG_MUTED,
             font=("微软雅黑", 9)).pack(side=tk.LEFT)
    ttk.Combobox(tech_row, textvariable=builder.ratio_var, values=OUTPUT_RATIOS,
                 state="readonly", width=10, font=("微软雅黑", 9)
                 ).pack(side=tk.LEFT, padx=(6, 0), ipady=3)
    builder.render_var.trace_add("write", lambda *_: builder._generate())
    builder.ratio_var.trace_add("write", lambda *_: builder._generate())

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
            command=lambda k=key: fill_negative_preset(builder, k),
        )
        b.pack(side=tk.LEFT, padx=(0, 6))
        tips = {"通用": "通用负面词\n追加常用负面词（模糊/低质/水印/多余文字/解剖错误等），适合所有风格。",
                "实拍专用": "实拍摄影负面词\n追加实拍摄影专用排除词（卡通/插画/手绘等风格偏差词）。",
                "动画专用": "动画/二次元负面词\n追加动漫/插画专用排除词（写实质感/照片感等风格偏差词）。"}
        Tooltip(b, tips.get(key, f"追加{label}负面词预设"))

    builder.neg_text = tk.Text(inner, bg=BG_CARD, fg=FG_MUTED,
                            insertbackground=FG_PRIMARY, relief=tk.FLAT,
                            font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
                            height=4)
    builder.neg_text.pack(fill=tk.X, padx=10, pady=(0, 10))
    builder.neg_text.bind("<KeyRelease>", lambda _e: builder._generate())


def refresh_detail_blocks(builder) -> None:
    if builder._quality_grid and builder._quality_grid.winfo_exists():
        fill_toggle_grid(
            builder,
            builder._quality_grid,
            builder.quality_toggles,
            QUALITY_CHIPS_ANIME if builder.is_anime.get() else QUALITY_CHIPS_REAL,
            cols=4,
        )
    if builder._texture_grid and builder._texture_grid.winfo_exists():
        fill_toggle_grid(
            builder,
            builder._texture_grid,
            builder.texture_toggles,
            TEXTURE_ANIME if builder.is_anime.get() else TEXTURE_REAL,
            cols=4,
        )
    if builder._color_grid and builder._color_grid.winfo_exists():
        fill_toggle_grid(
            builder,
            builder._color_grid,
            builder.color_toggles,
            COLOR_SUPPLEMENT_ANIME if builder.is_anime.get() else COLOR_SUPPLEMENT_REAL,
            cols=3,
        )
