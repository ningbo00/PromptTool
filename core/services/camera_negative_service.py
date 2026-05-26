def apply_negative_preset(current: str, key: str, presets: dict[str, str]) -> str:
    preset_text = presets.get(key, "")
    if not preset_text:
        return current
    current = current.strip()
    return f"{current}, {preset_text}" if current else preset_text
