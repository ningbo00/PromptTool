"""
prompts.json 的读写操作
"""
import json
import os
import sys

# ── 数据文件路径（支持打包后的 exe）─────────────────────────────
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _BASE_DIR = os.path.dirname(_BASE_DIR)   # shared/ 的上级 = 项目根

DATA_FILE = os.path.join(_BASE_DIR, "prompts.json")
CUSTOM_PRESETS_FILE = os.path.join(_BASE_DIR, "custom_presets.json")


def load_prompts():
    """读取 prompts.json，返回列表，异常时返回空列表"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    cleaned = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title   = str(item.get("title",   "")).strip()
        content = str(item.get("content", "")).strip()
        if title or content:
            cleaned.append({"title": title, "content": content})
    return cleaned


def save_prompts(prompts):
    """将 prompts 列表写入 prompts.json"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
