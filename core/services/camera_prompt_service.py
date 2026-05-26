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
