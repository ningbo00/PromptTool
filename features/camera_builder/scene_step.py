from shared import qt_compat as tk

from shared.ui_kit import (
    make_scroll_canvas, Tooltip, brick_span, prepare_brick_grid, place_brick,
    make_chip_button,
    BG_BASE, BG_CARD, BG_HOVER,
    FG_PRIMARY, FG_DIM, ACCENT_CYAN,
)
from features.camera_builder.presets import (
    SUBJECT_CHIPS_REAL, SUBJECT_CHIPS_ANIME,
    ENVIRONMENT_CHIPS_REAL, ENVIRONMENT_CHIPS_ANIME,
    WEATHER_CHIPS_REAL, WEATHER_CHIPS_ANIME,
    SUBJECT_COUNT_REAL, SUBJECT_COUNT_ANIME,
)


def create_scene_step(notebook, builder):
    step = tk.Frame(notebook, bg=BG_BASE)
    notebook.add(step, text="1 场景")
    builder.tab_subject = tk.Frame(step, bg=BG_BASE)
    builder.tab_subject.pack(fill=tk.BOTH, expand=True)
    return step


def build_subject_tab(builder):
    _, inner = make_scroll_canvas(builder.tab_subject, bg=BG_BASE)

    # ── 主体描述 ─────────────────────────────────────────────
    tk.Label(inner, text="✍ 主体描述", bg=BG_BASE, fg=ACCENT_CYAN,
             font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 2))

    builder.subject_text = tk.Text(inner, bg=BG_CARD, fg=FG_PRIMARY,
                                insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
                                height=3)
    builder.subject_text.pack(fill=tk.X, padx=10, pady=(0, 4))
    builder.subject_text.insert("1.0", builder._SUBJECT_HINT)
    builder.subject_text.config(fg=FG_DIM)
    builder.subject_text.bind("<FocusIn>",  lambda _e: builder._text_focus_in(builder.subject_text, builder._SUBJECT_HINT))
    builder.subject_text.bind("<FocusOut>", lambda _e: builder._text_focus_out(builder.subject_text, builder._SUBJECT_HINT))
    builder.subject_text.bind("<KeyRelease>", lambda _e: builder._generate())

    # 主体快捷词块
    tk.Label(inner, text="角色词块:", bg=BG_BASE, fg=FG_DIM,
             font=("微软雅黑", 8)).pack(anchor="w", padx=10)
    builder._subject_chips_frame = tk.Frame(inner, bg=BG_BASE)
    builder._subject_chips_frame.pack(fill=tk.X, padx=10, pady=(2, 4))
    fill_chips(builder, builder._subject_chips_frame, builder.subject_text,
                     SUBJECT_CHIPS_ANIME if builder.is_anime.get() else SUBJECT_CHIPS_REAL)

    # 人数词块
    tk.Label(inner, text="人数/关系:", bg=BG_BASE, fg=FG_DIM,
             font=("微软雅黑", 8)).pack(anchor="w", padx=10)
    builder._count_chips_frame = tk.Frame(inner, bg=BG_BASE)
    builder._count_chips_frame.pack(fill=tk.X, padx=10, pady=(2, 10))
    fill_chips(builder, builder._count_chips_frame, builder.subject_text,
                     SUBJECT_COUNT_ANIME if builder.is_anime.get() else SUBJECT_COUNT_REAL)

    # ── 场景环境 ─────────────────────────────────────────────
    tk.Label(inner, text="🌍 场景环境", bg=BG_BASE, fg=ACCENT_CYAN,
             font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 2))

    builder.environ_text = tk.Text(inner, bg=BG_CARD, fg=FG_PRIMARY,
                                insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
                                height=3)
    builder.environ_text.pack(fill=tk.X, padx=10, pady=(0, 4))
    builder.environ_text.insert("1.0", builder._ENVIRON_HINT)
    builder.environ_text.config(fg=FG_DIM)
    builder.environ_text.bind("<FocusIn>",  lambda _e: builder._text_focus_in(builder.environ_text, builder._ENVIRON_HINT))
    builder.environ_text.bind("<FocusOut>", lambda _e: builder._text_focus_out(builder.environ_text, builder._ENVIRON_HINT))
    builder.environ_text.bind("<KeyRelease>", lambda _e: builder._generate())

    # 场景快捷词块
    tk.Label(inner, text="场景词块:", bg=BG_BASE, fg=FG_DIM,
             font=("微软雅黑", 8)).pack(anchor="w", padx=10)
    builder._environ_chips_frame = tk.Frame(inner, bg=BG_BASE)
    builder._environ_chips_frame.pack(fill=tk.X, padx=10, pady=(2, 4))
    fill_chips(builder, builder._environ_chips_frame, builder.environ_text,
                     ENVIRONMENT_CHIPS_ANIME if builder.is_anime.get() else ENVIRONMENT_CHIPS_REAL)

    # 时间/天气词块
    tk.Label(inner, text="时间/天气:", bg=BG_BASE, fg=FG_DIM,
             font=("微软雅黑", 8)).pack(anchor="w", padx=10)
    builder._weather_chips_frame = tk.Frame(inner, bg=BG_BASE)
    builder._weather_chips_frame.pack(fill=tk.X, padx=10, pady=(2, 10))
    fill_chips(builder, builder._weather_chips_frame, builder.environ_text,
                     WEATHER_CHIPS_ANIME if builder.is_anime.get() else WEATHER_CHIPS_REAL)

def fill_chips(builder, frame, target_text, chips):
    for w in frame.winfo_children():
        w.destroy()
    total_units = 24
    prepare_brick_grid(frame, total_units=total_units, spacing=5)
    row_idx, col_idx = 0, 0
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
            font=("微软雅黑", 7), padx=6, pady=2, cursor="hand2",
            activebackground=BG_HOVER, wraplength=130, justify=tk.CENTER,
            command=lambda _checked=False, c=output, t=target_text: builder._append_chip(t, c),
        )
        make_chip_button(b, 38)
        span = brick_span(display, min_units=4, max_units=8)
        row_idx, col_idx = place_brick(
            b, row_idx, col_idx, span, total_units=total_units
        )
        if isinstance(chip, tuple):
            Tooltip(b, f"{chinese}\n英文：{output}\n点击追加到文本框。")
        else:
            Tooltip(b, f"{output}\n点击追加到文本框。")


def refresh_subject_chips(builder) -> None:
    if builder._subject_chips_frame and builder._subject_chips_frame.winfo_exists():
        fill_chips(
            builder,
            builder._subject_chips_frame,
            builder.subject_text,
            SUBJECT_CHIPS_ANIME if builder.is_anime.get() else SUBJECT_CHIPS_REAL,
        )
    if builder._count_chips_frame and builder._count_chips_frame.winfo_exists():
        fill_chips(
            builder,
            builder._count_chips_frame,
            builder.subject_text,
            SUBJECT_COUNT_ANIME if builder.is_anime.get() else SUBJECT_COUNT_REAL,
        )
    if builder._environ_chips_frame and builder._environ_chips_frame.winfo_exists():
        fill_chips(
            builder,
            builder._environ_chips_frame,
            builder.environ_text,
            ENVIRONMENT_CHIPS_ANIME if builder.is_anime.get() else ENVIRONMENT_CHIPS_REAL,
        )
    if builder._weather_chips_frame and builder._weather_chips_frame.winfo_exists():
        fill_chips(
            builder,
            builder._weather_chips_frame,
            builder.environ_text,
            WEATHER_CHIPS_ANIME if builder.is_anime.get() else WEATHER_CHIPS_REAL,
        )
