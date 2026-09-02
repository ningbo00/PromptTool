import json
import re
from dataclasses import dataclass, field
from pathlib import Path


PRESET_SCHEMA = "prompttool.preset.v1"
PRESET_TYPE = "style_preset"
MODE_REALISTIC = "realistic"
MODE_CARTOON = "cartoon"
PRESET_MODES = {MODE_REALISTIC, MODE_CARTOON}
ID_PATTERN = re.compile(r"^[a-z0-9_]+$")

_COMMON_PROMPT = """你是 PromptTool 的影视美术预设设计助手。

我会给你一个主题描述。请根据主题生成一个 PromptTool 可导入的 JSON 预设。

主题描述：
【在这里填写你的预设主题】

请严格遵守以下要求：

1. 只输出 JSON，不要解释，不要 Markdown，不要代码块。
2. JSON 必须是合法 JSON，不能有注释，不能有尾随逗号。
3. schema 固定为 "prompttool.preset.v1"。
4. type 固定为 "style_preset"。
5. preset_mode 固定为 "{mode}"。
6. id 使用英文小写、数字和下划线，必须能表达主题。
7. label 使用中文，适合显示在软件界面里。
8. category 使用中文分类。
9. description 用中文简短说明这个预设适合生成什么视觉风格。
10. 不要把预设写成一次性视频分镜，不要固定具体主体、具体动作、具体剧情。
11. 可以包含“风格化摄影语言”，但只能是长期稳定的摄影倾向，不能是具体镜头运动或单次机位。
12. 避免直接使用具体版权角色名、演员名、公司名、电影片名作为 prompt 核心；可以用视觉特征、世界观和美术语言替代。
13. 英文 prompt 词组要自然、可直接用于 AI 生图/生视频。
14. 每个数组建议 6-14 项，不要过短，也不要堆砌无关词。
15. negative_prompt 应该包含会破坏这个风格的负面词。
{mode_rules}

JSON 结构必须严格如下：

{{
  "schema": "prompttool.preset.v1",
  "type": "style_preset",
  "preset_mode": "{mode}",
  "id": "",
  "label": "",
  "category": "",
  "description": "",
  "visual_language": [],
  "rendering_profile": [],
  "cinematography_profile": [],
  "color_materials": [],
  "mood_atmosphere": [],
  "negative_prompt": [],
  "usage_notes": "",
  "do_not_include": []
}}

字段说明：

visual_language：
填写可复用的视觉美术语言，例如服装、建筑、道具、时代感、世界观、造型特征、质感方向。

rendering_profile：
填写渲染/媒介风格。写实预设可写 film still、live-action realism、practical effects 等；卡通预设必须重点填写 toon shading、stylized 3D、game CG、hand-painted texture 等。

cinematography_profile：
填写可复用的摄影风格倾向，例如 anamorphic framing、restrained camera movement、handheld realism、shallow depth of field、high contrast noir lighting。不要写具体镜头路径、具体机位、具体几秒动作。

color_materials：
填写颜色、材质、表面质感、光影质感。

mood_atmosphere：
填写情绪、氛围、叙事气质、世界观感受。

negative_prompt：
填写英文负面词，避免低质量、塑料感、卡通化、不符合该风格的内容。

usage_notes：
用中文说明这个预设适合如何叠加到用户主体和场景上。

do_not_include：
填写这个预设不应该强行包含的内容，例如固定人物、固定动作、具体版权角色名、具体演员脸、固定镜头时序等。

现在请根据我的主题描述生成 JSON。"""

DOUBAO_REALISTIC_PRESET_PROMPT = _COMMON_PROMPT.format(
    mode=MODE_REALISTIC,
    mode_rules=(
        "16. 这是写实/电影/摄影/真人 CG 预设，重点描述真实材质、电影美术、摄影语言、自然或戏剧光线。"
        "\n17. rendering_profile 可以填写写实渲染和电影质感，但不要写卡通、二次元、Q版、游戏UI风。"
    ),
)

DOUBAO_CARTOON_PRESET_PROMPT = _COMMON_PROMPT.format(
    mode=MODE_CARTOON,
    mode_rules=(
        "16. 这是卡通/动画/游戏 CG/二次元/3D 动画预设，必须重点填写 rendering_profile。"
        "\n17. rendering_profile 应描述造型语言、线条轮廓、toon shading、stylized 3D、hand-painted texture、game cinematic、色彩饱和度等。"
        "\n18. 不要写 photorealistic skin texture、真实摄影皮肤毛孔、真人演员脸。"
    ),
)

DOUBAO_PRESET_PROMPT = DOUBAO_REALISTIC_PRESET_PROMPT


@dataclass(frozen=True)
class CustomStylePreset:
    id: str
    label: str
    preset_mode: str
    category: str = ""
    description: str = ""
    visual_language: list[str] = field(default_factory=list)
    rendering_profile: list[str] = field(default_factory=list)
    cinematography_profile: list[str] = field(default_factory=list)
    color_materials: list[str] = field(default_factory=list)
    mood_atmosphere: list[str] = field(default_factory=list)
    negative_prompt: list[str] = field(default_factory=list)
    usage_notes: str = ""
    do_not_include: list[str] = field(default_factory=list)

    def to_json_dict(self) -> dict:
        return {
            "schema": PRESET_SCHEMA,
            "type": PRESET_TYPE,
            "preset_mode": self.preset_mode,
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "visual_language": self.visual_language,
            "rendering_profile": self.rendering_profile,
            "cinematography_profile": self.cinematography_profile,
            "color_materials": self.color_materials,
            "mood_atmosphere": self.mood_atmosphere,
            "negative_prompt": self.negative_prompt,
            "usage_notes": self.usage_notes,
            "do_not_include": self.do_not_include,
        }

    def to_camera_preset(self) -> dict:
        return {
            "_extra": ", ".join(
                self.visual_language
                + self.rendering_profile
                + self.cinematography_profile
                + self.color_materials
                + self.mood_atmosphere
            ),
            "_negative": ", ".join(self.negative_prompt),
            "_custom_preset_id": self.id,
            "_preset_mode": self.preset_mode,
            "_description": self.description,
            "_usage_notes": self.usage_notes,
        }


class PresetValidationError(ValueError):
    pass


class CustomPresetService:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> list[CustomStylePreset]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        raw_presets = data.get("presets", []) if isinstance(data, dict) else data
        if not isinstance(raw_presets, list):
            return []
        presets = []
        for item in raw_presets:
            try:
                presets.append(validate_style_preset(item))
            except PresetValidationError:
                continue
        return presets

    def save(self, presets: list[CustomStylePreset]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema": "prompttool.custom_presets.v1",
            "presets": [preset.to_json_dict() for preset in presets],
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def import_from_text(self, text: str) -> CustomStylePreset:
        try:
            data = json.loads(_strip_code_fence(text))
        except json.JSONDecodeError as exc:
            raise PresetValidationError(f"不是合法 JSON：{exc.msg}") from exc
        preset = validate_style_preset(data)
        presets = self.load()
        preset = _dedupe_preset(preset, {item.id for item in presets}, {item.label for item in presets})
        presets.append(preset)
        self.save(presets)
        return preset


def validate_style_preset(data) -> CustomStylePreset:
    if not isinstance(data, dict):
        raise PresetValidationError("JSON 根节点必须是对象。")
    if data.get("schema") != PRESET_SCHEMA:
        raise PresetValidationError(f"schema 必须是 {PRESET_SCHEMA}。")
    if data.get("type") != PRESET_TYPE:
        raise PresetValidationError(f"type 必须是 {PRESET_TYPE}。")
    preset_mode = str(data.get("preset_mode", "")).strip()
    if preset_mode not in PRESET_MODES:
        raise PresetValidationError("preset_mode 必须是 realistic 或 cartoon。")
    preset_id = str(data.get("id", "")).strip()
    if not preset_id or not ID_PATTERN.match(preset_id):
        raise PresetValidationError("id 只能包含英文小写、数字和下划线。")
    label = str(data.get("label", "")).strip()
    if not label:
        raise PresetValidationError("label 不能为空。")
    return CustomStylePreset(
        id=preset_id,
        label=label,
        preset_mode=preset_mode,
        category=str(data.get("category", "")).strip(),
        description=str(data.get("description", "")).strip(),
        visual_language=_string_list(data, "visual_language"),
        rendering_profile=_string_list(data, "rendering_profile", required=(preset_mode == MODE_CARTOON)),
        cinematography_profile=_string_list(data, "cinematography_profile"),
        color_materials=_string_list(data, "color_materials"),
        mood_atmosphere=_string_list(data, "mood_atmosphere"),
        negative_prompt=_string_list(data, "negative_prompt"),
        usage_notes=str(data.get("usage_notes", "")).strip(),
        do_not_include=_string_list(data, "do_not_include"),
    )


def camera_presets_from_custom(path: str | Path, preset_mode: str | None = None) -> dict[str, dict]:
    return {
        preset.label: preset.to_camera_preset()
        for preset in CustomPresetService(path).load()
        if preset_mode is None or preset.preset_mode == preset_mode
    }


def _string_list(data: dict, key: str, required: bool = True) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list):
        raise PresetValidationError(f"{key} 必须是字符串数组。")
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    if required and not cleaned and key != "do_not_include":
        raise PresetValidationError(f"{key} 不能为空。")
    return cleaned


def _dedupe_preset(
    preset: CustomStylePreset,
    existing_ids: set[str],
    existing_labels: set[str],
) -> CustomStylePreset:
    preset_id = preset.id
    label = preset.label
    suffix = 2
    while preset_id in existing_ids:
        preset_id = f"{preset.id}_{suffix}"
        suffix += 1
    suffix = 2
    while label in existing_labels:
        label = f"{preset.label} {suffix}"
        suffix += 1
    if preset_id == preset.id and label == preset.label:
        return preset
    return CustomStylePreset(
        id=preset_id,
        label=label,
        preset_mode=preset.preset_mode,
        category=preset.category,
        description=preset.description,
        visual_language=preset.visual_language,
        rendering_profile=preset.rendering_profile,
        cinematography_profile=preset.cinematography_profile,
        color_materials=preset.color_materials,
        mood_atmosphere=preset.mood_atmosphere,
        negative_prompt=preset.negative_prompt,
        usage_notes=preset.usage_notes,
        do_not_include=preset.do_not_include,
    )


def _strip_code_fence(text: str) -> str:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return raw
