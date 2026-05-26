from dataclasses import dataclass, field


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
