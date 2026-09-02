from shared import qt_compat as tk
from shared.qt_compat import ttk, messagebox
import pyperclip

from shared.ui_kit import (
    make_scroll_canvas, Tooltip, brick_span, prepare_brick_grid, place_brick,
    make_chip_button,
    BG_BASE, BG_SURFACE, BG_CARD, BG_HOVER,
    FG_PRIMARY, FG_MUTED, FG_DIM, ACCENT_BLUE, ACCENT_GREEN,
    ACCENT_PURPLE, ACCENT_YELLOW, DARK_TEXT,
)
from shared.storage import CUSTOM_PRESETS_FILE
from core.services.custom_preset_service import (
    CustomPresetService,
    DOUBAO_CARTOON_PRESET_PROMPT,
    DOUBAO_REALISTIC_PRESET_PROMPT,
    MODE_CARTOON,
    MODE_REALISTIC,
    PresetValidationError,
)
from features.camera_builder.extractor_actions import (
    append_extractor_extra,
    apply_extractor_style,
    clear_extractor_style,
    select_extractor_preset,
)
from features.camera_builder.presets import (
    FILTER_KEYWORDS, PRESETS_REAL, PRESETS_ANIME,
    STYLE_REAL, STYLE_ANIME, MOOD_REAL, MOOD_ANIME,
    MOTION_OPTIONS, AESTHETIC_REAL, AESTHETIC_ANIME,
)


def create_style_step(notebook, builder):
    step = tk.Frame(notebook, bg=BG_BASE)
    notebook.add(step, text="2 风格")
    inner = ttk.Notebook(step, style="Dark.TNotebook")
    inner.pack(fill=tk.BOTH, expand=True)

    builder.tab_preset = tk.Frame(inner, bg=BG_BASE)
    builder.tab_style = tk.Frame(inner, bg=BG_BASE)
    builder.tab_filter = tk.Frame(inner, bg=BG_BASE)
    builder.tab_extractor = tk.Frame(inner, bg=BG_BASE)
    inner.add(builder.tab_preset, text="预设")
    inner.add(builder.tab_style, text="情绪")
    inner.add(builder.tab_filter, text="滤镜")
    inner.add(builder.tab_extractor, text="提炼")
    return step


def build_preset_tab(builder):
    _, inner = make_scroll_canvas(builder.tab_preset, bg=BG_BASE)

    action_row = tk.Frame(inner, bg=BG_BASE)
    action_row.pack(fill=tk.X, padx=12, pady=(12, 8))
    copy_real_btn = tk.Button(
        action_row, text="复制写实模板",
        bg=BG_CARD, fg=ACCENT_BLUE, relief=tk.FLAT,
        font=("微软雅黑", 9, "bold"), padx=10, pady=4,
        cursor="hand2", activebackground=BG_HOVER,
        highlightbackground=ACCENT_BLUE, highlightthickness=1,
        command=lambda _checked=False: copy_doubao_preset_prompt(builder, MODE_REALISTIC),
    )
    copy_real_btn.pack(side=tk.LEFT, padx=(0, 8))
    Tooltip(copy_real_btn, "复制写实预设模板\n用于电影、摄影、真人 CG、写实美术风格。")
    copy_cartoon_btn = tk.Button(
        action_row, text="复制卡通模板",
        bg=BG_CARD, fg=ACCENT_PURPLE, relief=tk.FLAT,
        font=("微软雅黑", 9, "bold"), padx=10, pady=4,
        cursor="hand2", activebackground=BG_HOVER,
        highlightbackground=ACCENT_PURPLE, highlightthickness=1,
        command=lambda _checked=False: copy_doubao_preset_prompt(builder, MODE_CARTOON),
    )
    copy_cartoon_btn.pack(side=tk.LEFT, padx=(0, 8))
    Tooltip(copy_cartoon_btn, "复制卡通预设模板\n用于卡通、动画、游戏 CG、二次元、风格化 3D。")
    import_btn = tk.Button(
        action_row, text="从剪贴板导入预设",
        bg=BG_CARD, fg=ACCENT_GREEN, relief=tk.FLAT,
        font=("微软雅黑", 9, "bold"), padx=10, pady=4,
        cursor="hand2", activebackground=BG_HOVER,
        highlightbackground=ACCENT_GREEN, highlightthickness=1,
        command=lambda _checked=False: import_preset_from_clipboard(builder),
    )
    import_btn.pack(side=tk.LEFT)
    Tooltip(import_btn, "从剪贴板导入预设\n复制豆包返回的 JSON 后点击，导入为新的实拍预设。")

    tk.Label(inner, text="🎬 经典电影预设（实拍模式）", bg=BG_BASE, fg=ACCENT_BLUE,
             font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=12, pady=(4, 6))
    builder._real_preset_container = tk.Frame(inner, bg=BG_BASE)
    builder._real_preset_container.pack(fill=tk.X)
    make_preset_grid(builder, builder._real_preset_container, PRESETS_REAL, anime_mode=False)

    ttk.Separator(inner, orient="horizontal").pack(fill=tk.X, padx=12, pady=12)

    tk.Label(inner, text="🌸 动画风格预设（二次元模式）", bg=BG_BASE, fg=ACCENT_PURPLE,
             font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=12, pady=(0, 6))
    builder._anime_preset_container = tk.Frame(inner, bg=BG_BASE)
    builder._anime_preset_container.pack(fill=tk.X)
    make_preset_grid(builder, builder._anime_preset_container, PRESETS_ANIME, anime_mode=True)

    ttk.Separator(inner, orient="horizontal").pack(fill=tk.X, padx=12, pady=12)
    tk.Label(inner, text="💡 点击预设会自动切换模式并填充参数，之后可在参数页微调。",
             bg=BG_BASE, fg=FG_DIM, font=("微软雅黑", 9)).pack(anchor="w", padx=12, pady=(0, 12))


def copy_doubao_preset_prompt(builder, preset_mode=MODE_REALISTIC):
    prompt = DOUBAO_CARTOON_PRESET_PROMPT if preset_mode == MODE_CARTOON else DOUBAO_REALISTIC_PRESET_PROMPT
    pyperclip.copy(prompt)
    label = "卡通" if preset_mode == MODE_CARTOON else "写实"
    if hasattr(builder, "_flash_status"):
        builder._flash_status(f"豆包{label}预设模板已复制 ✓")
    else:
        messagebox.showinfo("提示", f"豆包{label}预设模板已复制到剪贴板。", parent=builder)


def import_preset_from_clipboard(builder):
    try:
        text = pyperclip.paste()
    except Exception as exc:
        messagebox.showinfo("导入失败", f"读取剪贴板失败：{exc}", parent=builder)
        return
    try:
        preset = CustomPresetService(CUSTOM_PRESETS_FILE).import_from_text(text)
    except PresetValidationError as exc:
        messagebox.showinfo("导入失败", str(exc), parent=builder)
        return
    from features.camera_builder import presets as preset_module

    preset_module.reload_custom_presets()
    builder._refresh_preset_tab()
    builder._apply_preset(preset.label, anime_mode=(preset.preset_mode == MODE_CARTOON))
    if hasattr(builder, "_flash_status"):
        builder._flash_status(f"已导入预设「{preset.label}」✓")
    else:
        messagebox.showinfo("导入成功", f"已导入预设「{preset.label}」。", parent=builder)

def make_preset_grid(builder, parent, presets_dict, anime_mode):
    from features.camera_builder.presets import PRESETS_REAL, PRESETS_ANIME
    grid = tk.Frame(parent, bg=BG_BASE)
    grid.pack(fill=tk.X, padx=12, pady=(0, 4))
    total_units = 24
    prepare_brick_grid(grid, total_units=total_units, spacing=5)
    row_idx, col_idx = 0, 0
    preset_data = PRESETS_ANIME if anime_mode else PRESETS_REAL
    custom_names = [name for name, data in presets_dict.items() if data.get("_custom_preset_id")]
    built_in_names = [name for name in presets_dict if name not in custom_names]
    ordered_names = custom_names + built_in_names
    for name in ordered_names:
        pdata = preset_data.get(name, {})
        tip_parts = [f"🎬 {name}"]
        if pdata.get("_description"):
            tip_parts.append(pdata["_description"])
        if "_extra" in pdata:
            tip_parts.append(f"风格词：{pdata['_extra'][:60]}…")
        if pdata.get("_negative"):
            tip_parts.append(f"负面词：{pdata['_negative'][:60]}…")
        tip_parts.append("点击应用此预设，自动填充所有参数。")
        b = tk.Button(
            grid, text=name, bg=BG_CARD, fg=FG_PRIMARY,
            relief=tk.FLAT, font=("微软雅黑", 8), padx=6, pady=2,
            cursor="hand2", activebackground=BG_HOVER,
            wraplength=200, justify=tk.LEFT,
            command=lambda _checked=False, n=name, a=anime_mode: builder._apply_preset(n, a),
        )
        make_chip_button(b, 36)
        row_idx, col_idx = place_brick(
            b, row_idx, col_idx, brick_span(name, min_units=4, max_units=8),
            total_units=total_units
        )
        Tooltip(b, "\n".join(tip_parts))

def build_style_tab(builder):
    _, inner = make_scroll_canvas(builder.tab_style, bg=BG_BASE)

    tk.Label(inner, text="🎨 风格", bg=BG_BASE, fg=ACCENT_BLUE,
             font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
    builder._style_grid = tk.Frame(inner, bg=BG_BASE)
    builder._style_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
    fill_toggle_grid(builder, builder._style_grid, builder.style_toggles,
                           STYLE_ANIME if builder.is_anime.get() else STYLE_REAL, cols=4)

    tk.Label(inner, text="🏛 美学流派", bg=BG_BASE, fg=ACCENT_PURPLE,
             font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
    builder._aesthetic_grid = tk.Frame(inner, bg=BG_BASE)
    builder._aesthetic_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
    fill_toggle_grid(builder, builder._aesthetic_grid, builder.aesthetic_toggles,
                           AESTHETIC_ANIME if builder.is_anime.get() else AESTHETIC_REAL, cols=4)

    tk.Label(inner, text="💫 情绪氛围", bg=BG_BASE, fg=ACCENT_YELLOW,
             font=("微软雅黑", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 4))
    builder._mood_grid = tk.Frame(inner, bg=BG_BASE)
    builder._mood_grid.pack(fill=tk.X, padx=10, pady=(0, 8))
    fill_toggle_grid(builder, builder._mood_grid, builder.mood_toggles,
                           MOOD_ANIME if builder.is_anime.get() else MOOD_REAL, cols=4)

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

    ttk.Combobox(motion_row, textvariable=builder.motion_var, values=MOTION_OPTIONS,
                 state="readonly", width=28, font=("微软雅黑", 9)
                 ).pack(side=tk.LEFT, padx=(8, 0), ipady=3)
    builder._motion_zh_lbl = tk.Label(motion_row, text="", bg=BG_BASE, fg=FG_MUTED,
                                   font=("微软雅黑", 8))
    builder._motion_zh_lbl.pack(side=tk.LEFT, padx=(8, 0))

    def _update_motion_zh(*_):
        zh = _MOTION_ZH.get(builder.motion_var.get(), "")
        builder._motion_zh_lbl.config(text=f"（{zh}）" if zh and zh != "（不指定）" else "")
        builder._generate()

    builder.motion_var.trace_add("write", _update_motion_zh)

def fill_toggle_grid(builder, grid_frame, toggles_dict, data, cols=4):
    # 保留已�� BoolVar 的状态（供风格提炼器等外部设置使用）
    saved_state = {kw: bv.get() for kw, bv in toggles_dict.items()}
    for w in grid_frame.winfo_children():
        w.destroy()
    toggles_dict.clear()
    total_units = 24
    prepare_brick_grid(grid_frame, total_units=total_units, spacing=5)
    row_i, col_i = 0, 0
    for kw, zh in data:
        bv = tk.BooleanVar(value=saved_state.get(kw, False))
        toggles_dict[kw] = bv
        btn_ref = [None]
        display = f"{kw}\n{zh}"

        def _toggle(_checked=False, b=bv, br=btn_ref):
            b.set(not b.get())
            br[0].config(bg=ACCENT_BLUE if b.get() else BG_CARD,
                         fg=DARK_TEXT if b.get() else FG_PRIMARY)
            builder._generate()

        btn = tk.Button(grid_frame, text=display, bg=BG_CARD, fg=FG_PRIMARY,
                        relief=tk.FLAT, font=("微软雅黑", 7), padx=6, pady=2,
                        cursor="hand2", activebackground=BG_HOVER,
                        wraplength=130, justify=tk.CENTER, command=_toggle)
        btn_ref[0] = btn
        make_chip_button(btn, 38)
        row_i, col_i = place_brick(
            btn, row_i, col_i, brick_span(display, min_units=4, max_units=8),
            total_units=total_units
        )
        Tooltip(btn, f"{zh}\n{kw}\n点击选中/取消，选中后加入生成结果。")


def refresh_style_blocks(builder) -> None:
    refresh_style_toggle_colors(builder)


def refresh_style_toggle_colors(builder) -> None:
    if builder._style_grid and builder._style_grid.winfo_exists():
        fill_toggle_grid(
            builder,
            builder._style_grid,
            builder.style_toggles,
            STYLE_ANIME if builder.is_anime.get() else STYLE_REAL,
            cols=4,
        )
    if builder._aesthetic_grid and builder._aesthetic_grid.winfo_exists():
        fill_toggle_grid(
            builder,
            builder._aesthetic_grid,
            builder.aesthetic_toggles,
            AESTHETIC_ANIME if builder.is_anime.get() else AESTHETIC_REAL,
            cols=4,
        )
    if builder._mood_grid and builder._mood_grid.winfo_exists():
        fill_toggle_grid(
            builder,
            builder._mood_grid,
            builder.mood_toggles,
            MOOD_ANIME if builder.is_anime.get() else MOOD_REAL,
            cols=4,
        )

def build_filter_tab(builder):
    builder.filter_toggles.clear()
    builder.filter_labels.clear()
    builder.filter_custom_vars.clear()

    _, inner = make_scroll_canvas(builder.tab_filter, bg=BG_BASE)
    tk.Label(inner, text="点击关键词选中（高亮），再点取消。每组下方可添加自定义词块。",
             bg=BG_BASE, fg=FG_DIM, font=("微软雅黑", 8)).pack(anchor="w", padx=10, pady=(8, 4))

    for category, words in FILTER_KEYWORDS.items():
        make_filter_group(builder, inner, category, words)

def make_filter_group(builder, parent, category, words):
    group = tk.Frame(parent, bg=BG_BASE)
    group.pack(fill=tk.X, padx=10, pady=(6, 2))

    tk.Label(group, text=category, bg=BG_BASE, fg=ACCENT_PURPLE,
             font=("微软雅黑", 9, "bold")).pack(anchor="w")

    btn_grid = tk.Frame(group, bg=BG_BASE)
    btn_grid.pack(fill=tk.X, pady=(4, 0))

    row_idx, col_idx, total_units = 0, 0, 24
    prepare_brick_grid(btn_grid, total_units=total_units, spacing=5)
    for display_label, english_keyword in words:
        bv = tk.BooleanVar(value=False)
        builder.filter_toggles[english_keyword] = bv
        builder.filter_labels[english_keyword] = display_label
        btn = make_toggle_btn(builder, btn_grid, display_label, english_keyword, bv)
        row_idx, col_idx = place_brick(
            btn, row_idx, col_idx,
            brick_span(display_label, min_units=4, max_units=8),
            total_units=total_units
        )

    custom_row = tk.Frame(group, bg=BG_BASE)
    custom_row.pack(fill=tk.X, pady=(6, 0))
    sv = tk.StringVar()
    builder.filter_custom_vars[category] = sv
    HINT = "自定义词块：中文 / english keyword"
    entry = tk.Entry(custom_row, textvariable=sv, bg=BG_CARD, fg=FG_DIM,
                     insertbackground=FG_PRIMARY, relief=tk.FLAT, font=("微软雅黑", 9))
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
    entry.insert(0, HINT)
    entry.bind("<FocusIn>",  lambda _e, ent=entry, h=HINT: builder._hint_focus_in(ent, h))
    entry.bind("<FocusOut>", lambda _e, ent=entry, h=HINT: builder._hint_focus_out(ent, h))
    tk.Button(custom_row, text="+ 添加", bg=ACCENT_BLUE, fg=DARK_TEXT, relief=tk.FLAT,
              font=("微软雅黑", 8, "bold"), padx=10, pady=3, cursor="hand2",
              activebackground=ACCENT_BLUE,
              command=lambda _checked=False, bg=btn_grid, ent=entry, ri=[row_idx], ci=[col_idx], co=total_units:
                  add_custom_filter_btn(builder, bg, ent, ri, ci, co)
              ).pack(side=tk.LEFT, padx=(6, 0))

def make_toggle_btn(builder, parent, display_label, english_keyword, bv):
    btn_ref = [None]
    def toggle():
        bv.set(not bv.get())
        btn_ref[0].config(
            bg=ACCENT_PURPLE if bv.get() else BG_CARD,
            fg=DARK_TEXT if bv.get() else FG_PRIMARY,
        )
        builder._generate()
    b = tk.Button(parent, text=display_label, bg=BG_CARD, fg=FG_PRIMARY,
                  relief=tk.FLAT, font=("微软雅黑", 7), padx=6, pady=2,
                  cursor="hand2", activebackground=BG_HOVER,
                  wraplength=150, justify=tk.CENTER, command=toggle)
    make_chip_button(b, 36)
    btn_ref[0] = b
    Tooltip(b, f"英文关键词：{english_keyword}\n点击选中（高亮），再点取消。选中后加入生成结果。")
    return b

def add_custom_filter_btn(builder, grid_frame, entry, row_idx_ref, col_idx_ref, total_units):
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
    if english_keyword in builder.filter_toggles:
        return
    bv = tk.BooleanVar(value=True)
    builder.filter_toggles[english_keyword] = bv
    builder.filter_labels[english_keyword] = display_label
    btn = make_toggle_btn(builder, grid_frame, display_label, english_keyword, bv)
    btn.config(bg=ACCENT_PURPLE, fg=DARK_TEXT)
    ri, ci = row_idx_ref[0], col_idx_ref[0]
    ri, ci = place_brick(
        btn, ri, ci, brick_span(display_label, min_units=4, max_units=8),
        total_units=total_units
    )
    row_idx_ref[0], col_idx_ref[0] = ri, ci
    entry.delete(0, tk.END)
    entry.insert(0, HINT)
    entry.config(fg=FG_DIM)
    builder._generate()

def build_extractor_tab(builder):
    from features.camera_builder.presets import ANIME_STYLE_EXTRACTOR_PRESETS
    builder._extractor_presets = ANIME_STYLE_EXTRACTOR_PRESETS

    builder._extractor_detail_var = tk.StringVar(value="")
    builder._extractor_btn_refs = {}   # idx → button widget，用于高亮选中

    # ── 左右可调分栏 ──────────────────────────────────────────
    h_paned = ttk.PanedWindow(builder.tab_extractor, orient=tk.HORIZONTAL)
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
    for i, preset in enumerate(builder._extractor_presets):
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
                command=lambda _checked=False, idx=i: select_extractor_preset(builder, idx),
            )
            b.pack(side=tk.LEFT, padx=(0, 6), pady=2)
            builder._extractor_btn_refs[i] = b

    # ── 右侧：风格详情 + 操作按钮 ────────────────────────────
    right_host = tk.Frame(h_paned, bg=BG_BASE)
    h_paned.add(right_host, weight=1)

    right_top = tk.Frame(right_host, bg=BG_BASE)
    right_top.pack(fill=tk.X, padx=10, pady=(10, 4))
    tk.Label(right_top, text="风格详情", bg=BG_BASE, fg=ACCENT_YELLOW,
             font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
    builder._extractor_match_lbl = tk.Label(right_top, text="", bg=BG_BASE,
                                          fg=ACCENT_GREEN, font=("微软雅黑", 8))
    builder._extractor_match_lbl.pack(side=tk.LEFT, padx=(8, 0))

    builder._extractor_detail_text = tk.Text(
        right_host, bg=BG_SURFACE, fg=FG_PRIMARY, relief=tk.FLAT,
        font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
        state=tk.DISABLED,
    )
    builder._extractor_detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

    # 操作按钮行
    act_row = tk.Frame(right_host, bg=BG_BASE)
    act_row.pack(fill=tk.X, padx=10, pady=(0, 6))

    builder._extractor_apply_btn = tk.Button(
        act_row, text="🎭 应用风格词块", bg=ACCENT_BLUE, fg=DARK_TEXT,
        relief=tk.FLAT, font=("微软雅黑", 9, "bold"), padx=12, pady=4,
        cursor="hand2", activebackground=ACCENT_BLUE,
        state=tk.DISABLED,
        command=lambda _checked=False: apply_extractor_style(builder),
    )
    builder._extractor_apply_btn.pack(side=tk.LEFT, padx=(0, 6))
    Tooltip(builder._extractor_apply_btn,
            "🎭 应用风格词块\n将当前风格预设的关键词激活到[风格情绪]页签对应的词块上，并自动跳转到风格情绪页签。")

    tk.Button(
        act_row, text="➕ 追加到附加词", bg=ACCENT_GREEN, fg=DARK_TEXT,
        relief=tk.FLAT, font=("微软雅黑", 9, "bold"), padx=12, pady=4,
        cursor="hand2", activebackground=ACCENT_GREEN,
        command=lambda _checked=False: append_extractor_extra(builder),
    ).pack(side=tk.LEFT, padx=(0, 6))
    Tooltip(act_row.winfo_children()[-1],
            "➕ 追加到附加词\n将预设的所有关键词追加到右侧预览的附加词输入框，直接加入最终 Prompt 而不激活词块。")

    tk.Button(
        act_row, text="🗑 清除已选风格", bg=BG_HOVER, fg=FG_PRIMARY,
        relief=tk.FLAT, font=("微软雅黑", 8), padx=10, pady=4,
        cursor="hand2", activebackground=BG_HOVER,
        command=lambda _checked=False: clear_extractor_style(builder),
    ).pack(side=tk.LEFT)
    Tooltip(act_row.winfo_children()[-1],
            "🗑 清除已选风格\n取消[风格情绪]页签中所有已激活的风格/美学/情绪词块，恢复全部为未选状态。")

    # 延迟设置分割位置为 50%
    builder.after(30, lambda p=h_paned: p.sash_place(0, builder.tab_extractor.winfo_width() // 2, 0))
