import tkinter as tk

from core.services.camera_extractor_service import (
    append_keywords_to_extra,
    build_extractor_detail,
    count_keyword_matches,
    matched_keywords_by_group,
)
from shared.ui_kit import ACCENT_PURPLE, BG_CARD, DARK_TEXT, FG_PRIMARY


def select_extractor_preset(builder, idx: int) -> None:
    builder._extractor_selected_idx = idx
    preset = builder._extractor_presets[idx]
    if not hasattr(builder, "_extractor_detail_text") or builder._extractor_detail_text is None:
        return

    for button_idx, btn in builder._extractor_btn_refs.items():
        btn.config(
            bg=ACCENT_PURPLE if button_idx == idx else BG_CARD,
            fg=DARK_TEXT if button_idx == idx else FG_PRIMARY,
        )

    builder._extractor_detail_text.config(state=tk.NORMAL)
    builder._extractor_detail_text.delete("1.0", tk.END)
    builder._extractor_detail_text.insert("1.0", build_extractor_detail(preset))
    builder._extractor_detail_text.config(state=tk.DISABLED)

    keywords = preset.get("keywords", [])
    match_count = count_keyword_matches(
        keywords,
        list(builder.style_toggles),
        list(builder.aesthetic_toggles),
        list(builder.mood_toggles),
    )
    if hasattr(builder, "_extractor_match_lbl"):
        builder._extractor_match_lbl.config(
            text=f"可匹配 {match_count} 个词块"
            if match_count else "（无匹配词块，建议用[追加到附加词]）"
        )

    if hasattr(builder, "_extractor_apply_btn"):
        builder._extractor_apply_btn.config(state=tk.NORMAL)


def apply_extractor_style(builder) -> None:
    if builder._extractor_selected_idx is None:
        return
    preset = builder._extractor_presets[builder._extractor_selected_idx]
    matches = matched_keywords_by_group(
        preset.get("keywords", []),
        {
            "style": list(builder.style_toggles),
            "aesthetic": list(builder.aesthetic_toggles),
            "mood": list(builder.mood_toggles),
        },
    )
    _set_matches(builder.style_toggles, matches["style"])
    _set_matches(builder.aesthetic_toggles, matches["aesthetic"])
    _set_matches(builder.mood_toggles, matches["mood"])
    builder._refresh_style_toggle_colors()
    builder._generate()
    if builder.nb and builder.tab_style:
        try:
            builder.nb.select(builder.tab_style)
        except Exception:
            pass


def clear_extractor_style(builder) -> None:
    for toggle_group in [builder.style_toggles, builder.aesthetic_toggles, builder.mood_toggles]:
        for bv in toggle_group.values():
            bv.set(False)
    builder._refresh_style_toggle_colors()
    builder._generate()


def append_extractor_extra(builder) -> None:
    if builder._extractor_selected_idx is None:
        return
    preset = builder._extractor_presets[builder._extractor_selected_idx]
    builder.extra_var.set(
        append_keywords_to_extra(builder.extra_var.get(), preset.get("keywords", []))
    )
    builder._generate()


def _set_matches(toggle_group: dict, matches: set[str]) -> None:
    for keyword, bv in toggle_group.items():
        if keyword in matches:
            bv.set(True)
