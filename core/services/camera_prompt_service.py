from dataclasses import dataclass, field


@dataclass(frozen=True)
class PresetResolution:
    extra: str
    param_values: dict[str, str]
    custom_values: dict[str, str]


@dataclass(frozen=True)
class CameraPromptSpec:
    subject: str = ""
    environment: str = ""
    parameters: list[str] = field(default_factory=list)
    camera_terms: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    style_terms: list[str] = field(default_factory=list)
    detail_terms: list[str] = field(default_factory=list)
    render: str = ""
    ratio: str = ""
    extra: str = ""


def build_camera_prompt(spec: CameraPromptSpec) -> str:
    parts = []
    groups = [
        [spec.subject, spec.environment],
        spec.parameters,
        spec.camera_terms,
        spec.filters,
        spec.style_terms,
        spec.detail_terms,
        [_render_value(spec.render), _ratio_value(spec.ratio), spec.extra],
    ]
    for group in groups:
        for value in group:
            normalized = _normalize(value)
            if normalized:
                parts.append(normalized)
    return ", ".join(parts)


def append_negative_as_positive(base_prompt: str, negative_text: str) -> str:
    exclusion_parts = []
    for term in negative_text.split(","):
        term = term.strip()
        if not term:
            continue
        if term.startswith("(") and ":1." in term:
            exclusion_parts.append(term.replace(":1.", ":0."))
        elif term.lower().startswith("no ") or term.lower().startswith("avoid"):
            exclusion_parts.append(term)
        else:
            exclusion_parts.append(f"no {term}")
    if not exclusion_parts:
        return base_prompt
    return (
        f"{base_prompt}, {', '.join(exclusion_parts)}"
        if base_prompt else ", ".join(exclusion_parts)
    )


def build_negative_zh(negative_text: str, zh_map: dict, fallback) -> str:
    lines = []
    for term in negative_text.split(","):
        term = term.strip()
        if not term:
            continue
        if term.startswith("(") and ":" in term:
            inner = term.lstrip("(").split(":")[0].strip()
            weight_text = term.split(":")[-1].rstrip(")")
            try:
                weight = float(weight_text)
                zh = zh_map.get(inner.lower(), fallback(inner))
                lines.append(f"⚡强力压制：{zh}" if weight >= 1.3 else f"压制：{zh}")
            except ValueError:
                lines.append(zh_map.get(inner.lower(), fallback(inner)))
        else:
            fallback_zh = fallback(term)
            lines.append(zh_map.get(term.lower(), fallback_zh if fallback_zh != term else term))
    return "\n".join(lines)


def build_subject_scene_zh(subject: str = "", environment: str = "") -> str:
    parts = []
    subject = _normalize(subject)
    environment = _normalize(environment)
    if subject:
        parts.append(f"【主体描述】{subject}")
    if environment:
        parts.append(f"【场景环境】{environment}")
    return "\n".join(parts)


def build_style_mood_zh(
    styles: list[str],
    aesthetics: list[str],
    moods: list[str],
    motion: str,
    style_map: dict[str, str],
    aesthetic_map: dict[str, str],
    mood_map: dict[str, str],
    fallback,
) -> str:
    parts = []
    if styles:
        parts.append(f"【风格】{' / '.join(style_map.get(value, value) for value in styles)}")
    if aesthetics:
        parts.append(f"【美学流派】{' / '.join(aesthetic_map.get(value, value) for value in aesthetics)}")
    if moods:
        parts.append(f"【情绪氛围】{' / '.join(mood_map.get(value, value) for value in moods)}")
    motion = _normalize(motion)
    if motion and motion != "（不指定）":
        parts.append(f"【动作动态】{fallback(motion)}")
    return "\n".join(parts)


def build_detail_tech_zh(
    qualities: list[str],
    textures: list[str],
    colors: list[str],
    render: str,
    ratio: str,
    quality_map: dict[str, str],
    texture_map: dict[str, str],
    color_map: dict[str, str],
) -> str:
    parts = []
    if qualities:
        parts.append(f"【质量词块】{' / '.join(quality_map.get(value, value) for value in qualities)}")
    if textures:
        parts.append(f"【细节质感】{' / '.join(texture_map.get(value, value) for value in textures)}")
    if colors:
        parts.append(f"【色彩补充】{' / '.join(color_map.get(value, value) for value in colors)}")
    render = _render_value(render)
    ratio = _normalize(ratio)
    if render:
        parts.append(f"【渲染引擎】{render}")
    if ratio and ratio != "（不指定）":
        parts.append(f"【输出比例】{ratio}")
    return "\n".join(parts)


def build_prompt_zh(
    mode: str,
    subject_scene: str = "",
    params: list[str] | None = None,
    camera: list[str] | None = None,
    filters: list[str] | None = None,
    style_mood: str = "",
    detail_tech: str = "",
    extra: str = "",
) -> str:
    lines = []
    for value in [subject_scene, *(params or []), *(camera or [])]:
        if value:
            lines.append(value)
    if filters:
        lines.append(f"【滤镜效果】{' / '.join(filters)}")
    for value in [style_mood, detail_tech]:
        if value:
            lines.append(value)
    extra = _normalize(extra)
    if extra:
        lines.append(f"【附加词】{extra}")
    header = f"═══ 中文参数对照（{mode}模式）═══\n"
    return header + ("\n".join(lines) if lines else "（暂无启用参数）")


def resolve_preset_values(preset: dict, param_options: dict[str, list[str]]) -> PresetResolution:
    param_values = {}
    custom_values = {}
    for name, value in preset.items():
        if name == "_extra" or name not in param_options:
            continue
        options = param_options[name]
        match = next((option for option in options if option == value), None)
        if match is None:
            match = next((option for option in options if value in option or option in value), None)
        if match:
            param_values[name] = match
        else:
            custom_values[name] = value
    return PresetResolution(
        extra=preset.get("_extra", ""),
        param_values=param_values,
        custom_values=custom_values,
    )


def _render_value(value: str) -> str:
    value = _normalize(value)
    return "" if value == "（不指定）" else value


def _ratio_value(value: str) -> str:
    value = _normalize(value)
    if not value or value == "（不指定）":
        return ""
    return f"aspect ratio {value}"


def _normalize(value: str) -> str:
    return str(value).strip()
