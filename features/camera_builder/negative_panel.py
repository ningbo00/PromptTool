from shared import qt_compat as tk

from core.services.camera_negative_service import apply_negative_preset
from features.camera_builder.presets import NEG_PRESETS


def fill_negative_preset(builder, key: str) -> None:
    if builder.neg_text is None:
        return
    current = builder.neg_text.get("1.0", tk.END).strip()
    updated = apply_negative_preset(current, key, NEG_PRESETS)
    if updated == current:
        return
    builder.neg_text.delete("1.0", tk.END)
    builder.neg_text.insert("1.0", updated)
    builder._generate()
