from shared.global_hotkeys import (
    MOD_ALT,
    MOD_CONTROL,
    MOD_SHIFT,
    key_to_vk,
    normalize_hotkey,
    parse_hotkey,
)


def test_normalize_hotkey_uses_qt_portable_text():
    assert normalize_hotkey(" ctrl+alt+1 ") == "Ctrl+Alt+1"
    assert normalize_hotkey("") == ""


def test_parse_hotkey_maps_common_shortcuts_to_windows_values():
    assert parse_hotkey("Ctrl+Alt+1") == (MOD_CONTROL | MOD_ALT, ord("1"))
    assert parse_hotkey("Ctrl+Shift+S") == (MOD_CONTROL | MOD_SHIFT, ord("S"))
    assert parse_hotkey("F8") == (0, 0x77)


def test_key_to_vk_supports_named_keys():
    assert key_to_vk("Esc") == 0x1B
    assert key_to_vk("Del") == 0x2E
