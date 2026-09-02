"""Screenshot selection and image-to-prompt helpers."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPoint, QRect, Qt
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PySide6.QtWidgets import QWidget

from features.ai_optimize.client import call_ai
import shared.config as cfg


@dataclass(frozen=True)
class ScreenshotAnalysisMode:
    key: str
    label: str
    title_prefix: str
    description: str
    focus: str
    user_instruction: str


SCREENSHOT_ANALYSIS_MODES: dict[str, ScreenshotAnalysisMode] = {
    "full_reverse": ScreenshotAnalysisMode(
        key="full_reverse",
        label="完整反推",
        title_prefix="截图完整反推",
        description="生成一段可直接用于生图/生视频的完整英文 Prompt。",
        focus="subject, scene, composition, camera, lighting, color palette, style, texture, mood, quality tags",
        user_instruction="Reverse-engineer a concise, production-ready image/video generation prompt from this screenshot.",
    ),
    "character": ScreenshotAnalysisMode(
        key="character",
        label="角色反推",
        title_prefix="截图角色反推",
        description="只抓角色设定：外观、服装、材质、道具、气质，少写背景。",
        focus="character silhouette, face, hair, body type, outfit layers, accessories, materials, surface wear, personality, art style",
        user_instruction="Focus on the character design only. Avoid over-describing the background.",
    ),
    "scene": ScreenshotAnalysisMode(
        key="scene",
        label="场景反推",
        title_prefix="截图场景反推",
        description="只抓环境/世界观：地点、建筑、空间层次、氛围、道具、材质。",
        focus="location, architecture, foreground, midground, background, props, terrain, materials, atmosphere, worldbuilding details",
        user_instruction="Focus on the environment and worldbuilding. Do not invent character identities.",
    ),
    "cinematography": ScreenshotAnalysisMode(
        key="cinematography",
        label="镜头语言",
        title_prefix="截图镜头语言",
        description="分析镜头设置：景别、角度、构图、镜头倾向、景深、运动感。",
        focus="shot size, camera angle, framing, lens tendency, focal length feel, depth of field, perspective, camera movement language",
        user_instruction="Focus on cinematography and camera language, not story explanation.",
    ),
    "lighting_color": ScreenshotAnalysisMode(
        key="lighting_color",
        label="光色分析",
        title_prefix="截图光色分析",
        description="分析灯光和调色：主光/辅光/轮廓光、色温、对比、色彩方案。",
        focus="key light, fill light, rim light, light direction, softness, color temperature, palette, grading, contrast, exposure",
        user_instruction="Focus on lighting design and color grading.",
    ),
    "costume_props": ScreenshotAnalysisMode(
        key="costume_props",
        label="服装道具",
        title_prefix="截图服装道具",
        description="提取服装、盔甲、武器、工具、饰品、材质和磨损细节。",
        focus="costume layers, armor, weapons, tools, props, accessories, material language, weathering, decals, small surface details",
        user_instruction="Focus on costume, props, accessories, and material details.",
    ),
    "composition": ScreenshotAnalysisMode(
        key="composition",
        label="构图版式",
        title_prefix="截图构图版式",
        description="分析画面结构：视觉层级、主体位置、留白、引导线、海报式布局。",
        focus="visual hierarchy, subject placement, negative space, leading lines, balance, rhythm, poster/key-art layout, crop ratio",
        user_instruction="Focus on composition and layout structure.",
    ),
    "negative": ScreenshotAnalysisMode(
        key="negative",
        label="负面词反推",
        title_prefix="截图负面词",
        description="输出负面 Prompt，用于避免截图里不想要或容易破坏画面的缺陷。",
        focus="artifacts to avoid, anatomy errors, bad hands, noisy texture, low detail, distorted perspective, unwanted clutter, style-breaking issues",
        user_instruction="Generate only a negative prompt list for avoiding artifacts and style-breaking problems.",
    ),
    "custom": ScreenshotAnalysisMode(
        key="custom",
        label="自定义",
        title_prefix="截图自定义分析",
        description="按你在截图设置里输入的自定义要求分析截图。",
        focus="the user's custom screenshot analysis instruction",
        user_instruction="Follow the user's custom analysis instruction exactly.",
    ),
}

REVERSE_PROMPT_SYSTEM = (
    "你是专业的图像/视频生成 Prompt 反推专家。根据用户框选的截图，"
    "输出可直接用于 AI 生图/生视频的英文 Prompt。不要解释，不要 Markdown。"
)


def get_screenshot_analysis_mode(mode: str | None = None) -> ScreenshotAnalysisMode:
    key = mode or cfg.SCREENSHOT_ANALYSIS_MODE
    return SCREENSHOT_ANALYSIS_MODES.get(key, SCREENSHOT_ANALYSIS_MODES["full_reverse"])


def screenshot_analysis_label(mode: str | None = None) -> str:
    return get_screenshot_analysis_mode(mode).label


def screenshot_detail_label(detail: str | None = None) -> str:
    return "精简" if (detail or cfg.SCREENSHOT_PROMPT_DETAIL) == "concise" else "完整"


def build_screenshot_analysis_system(
    mode: str | None = None,
    custom: str | None = None,
    detail: str | None = None,
) -> str:
    spec = get_screenshot_analysis_mode(mode)
    custom_text = (custom if custom is not None else cfg.SCREENSHOT_ANALYSIS_CUSTOM).strip()
    detail_key = detail or cfg.SCREENSHOT_PROMPT_DETAIL
    detail_rule = (
        "英文 Prompt 控制在 30-55 个英文词，直接可用于图片生成，避免长句和解释。"
        if detail_key == "concise"
        else "英文 Prompt 可以更完整，包含主体、场景、构图、镜头、光线、色彩、风格、质感和质量词。"
    )
    if spec.key == "negative":
        output_rule = "输出英文 negative prompt，并给出中文预览。"
    elif spec.key == "custom" and custom_text:
        output_rule = "优先遵守用户自定义要求；除非自定义要求改变语言，否则仍要给出英文 Prompt 和中文预览。"
    else:
        output_rule = "输出英文 Prompt 和中文预览。"
    custom_rule = f"\n用户自定义要求：{custom_text}" if spec.key == "custom" and custom_text else ""
    return (
        f"{REVERSE_PROMPT_SYSTEM}\n"
        f"当前分析模式：{spec.label}。\n"
        f"重点关注：{spec.focus}。\n"
        f"长度要求：{detail_rule}\n"
        f"{output_rule}\n"
        "固定输出格式：\n"
        "English Prompt: <English prompt>\n"
        "中文预览：<中文翻译预览>\n"
        "不要输出 Markdown，不要额外解释。"
        f"{custom_rule}"
    )

def pixmap_to_png_bytes(pixmap: QPixmap) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def build_reverse_prompt_messages(
    png_bytes: bytes,
    mode: str | None = None,
    custom: str | None = None,
    detail: str | None = None,
) -> list[dict]:
    spec = get_screenshot_analysis_mode(mode)
    image_b64 = base64.b64encode(png_bytes).decode("ascii")
    custom_text = (custom if custom is not None else cfg.SCREENSHOT_ANALYSIS_CUSTOM).strip()
    user_text = spec.user_instruction
    if spec.key == "custom" and custom_text:
        user_text = custom_text
    return [
        {"role": "system", "content": build_screenshot_analysis_system(spec.key, custom_text, detail)},
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_text,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
            ],
        },
    ]


def is_probable_vision_model(model: str) -> bool:
    return cfg.is_screenshot_model_name(cfg.SCREENSHOT_PROVIDER, model)


def resolve_reverse_prompt_config() -> tuple[str, str, str, str]:
    provider = cfg.AI_PROVIDERS.get(cfg.SCREENSHOT_PROVIDER, cfg.AI_PROVIDERS["bailian"])
    key = getattr(cfg, provider.api_key_attr, "")
    configured_model = cfg.SCREENSHOT_MODEL
    if is_probable_vision_model(configured_model):
        return provider.url, key, configured_model, ""
    fallback = cfg.DEFAULT_SCREENSHOT_MODELS.get(provider.key, "")
    if fallback:
        return (
            provider.url,
            key,
            fallback,
            f"截图模型 {configured_model or '未设置'} 可能不支持图片输入，已自动改用视觉模型 {fallback}。",
        )
    return provider.url, key, configured_model, (
        f"截图服务商 {provider.label} 没有配置可用的视觉模型。"
        "请在 AI 设置中为截图分析选择 OpenAI / 阿里百炼 / Kimi / 豆包的视觉模型。"
    )


def call_reverse_prompt(png_bytes: bytes, on_success, on_error, on_model=None) -> None:
    url, key, model, note = resolve_reverse_prompt_config()
    if not key:
        provider = cfg.AI_PROVIDERS.get(cfg.SCREENSHOT_PROVIDER, cfg.AI_PROVIDERS["bailian"])
        on_error(f"请先在 AI 设置中填写截图服务商 {provider.label} 的 API Key。")
        return
    if not model:
        on_error(note or "没有可用的视觉模型。")
        return
    if on_model:
        on_model(model, note)
    if note and "没有配置" in note:
        on_error(note)
        return
    call_ai(
        url,
        key,
        model,
        build_reverse_prompt_messages(
            png_bytes,
            mode=cfg.SCREENSHOT_ANALYSIS_MODE,
            custom=cfg.SCREENSHOT_ANALYSIS_CUSTOM,
            detail=cfg.SCREENSHOT_PROMPT_DETAIL,
        ),
        temperature=0.35,
        on_success=on_success,
        on_error=on_error,
        max_tokens=700,
        timeout_s=120,
    )


def screenshot_prompt_title(mode: str | None = None) -> str:
    return get_screenshot_analysis_mode(mode).title_prefix + " " + datetime.now().strftime("%H:%M")


def format_reverse_prompt_result(text: str) -> str:
    """Normalize model output so the saved prompt always has a Chinese preview slot."""
    content = (text or "").strip()
    if not content:
        return ""
    if "中文预览" in content or "Chinese Preview" in content:
        return content
    return f"English Prompt: {content}\n\n中文预览：待生成中文预览（模型未返回翻译）。"


def normalize_shortcut(sequence: str, default: str = "Ctrl+Shift+S") -> str:
    """Normalize a shortcut string for Qt and fall back when invalid."""
    raw = (sequence or "").strip()
    if not raw:
        raw = default
    key_sequence = QKeySequence(raw)
    normalized = key_sequence.toString(QKeySequence.PortableText)
    return normalized or default


class ScreenshotSelector(QWidget):
    """Fullscreen overlay that lets the user drag a rectangular screen region."""

    def __init__(self, on_selected, on_cancel=None):
        super().__init__(None)
        self._on_selected = on_selected
        self._on_cancel = on_cancel
        self._start = QPoint()
        self._end = QPoint()
        self._dragging = False
        self._finished = False
        self._screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self._shot = self._screen.grabWindow(0) if self._screen else QPixmap()

        if self._screen:
            self.setGeometry(self._screen.geometry())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.showFullScreen()
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.ActiveWindowFocusReason)
        self.grabKeyboard()
        self._escape_shortcut = QShortcut(QKeySequence("Esc"), self)
        self._escape_shortcut.setContext(Qt.ApplicationShortcut)
        self._escape_shortcut.activated.connect(self._cancel)

    def paintEvent(self, _event):
        painter = QPainter(self)
        if not self._shot.isNull():
            painter.drawPixmap(self.rect(), self._shot)

        if self._dragging:
            rect = QRect(self._start, self._end).normalized()
            overlay = QColor(0, 0, 0, 115)
            # Keep the selected area untouched. Redrawing it from the pixmap can
            # become magnified on high-DPI screens because grabWindow uses
            # physical pixels while mouse coordinates are logical pixels.
            painter.fillRect(0, 0, self.width(), rect.top(), overlay)
            painter.fillRect(0, rect.bottom(), self.width(), self.height() - rect.bottom(), overlay)
            painter.fillRect(0, rect.top(), rect.left(), rect.height(), overlay)
            painter.fillRect(rect.right(), rect.top(), self.width() - rect.right(), rect.height(), overlay)
            painter.setPen(QPen(QColor("#3794ff"), 2))
            painter.drawRect(rect)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 115))
            painter.setPen(QColor("#e6e6e6"))
            painter.drawText(24, 36, "拖拽框选截图区域，Esc / 右键取消")

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._cancel()
            return
        if event.button() == Qt.LeftButton:
            self._start = event.position().toPoint()
            self._end = self._start
            self._dragging = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or not self._dragging:
            return
        self._dragging = False
        rect = QRect(self._start, event.position().toPoint()).normalized()
        if rect.width() < 12 or rect.height() < 12:
            self._cancel()
            return
        selected = self._shot.copy(self._source_rect(rect))
        selected.setDevicePixelRatio(1.0)
        self._finish(selected)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._cancel()
        else:
            super().keyPressEvent(event)

    def _cancel(self):
        self._finish(None)

    def _finish(self, selected: QPixmap | None):
        if self._finished:
            return
        self._finished = True
        self.releaseKeyboard()
        self.close()
        self.deleteLater()
        if selected is None:
            if self._on_cancel:
                self._on_cancel()
        else:
            self._on_selected(selected)

    def closeEvent(self, event):
        self.releaseKeyboard()
        super().closeEvent(event)

    def _source_rect(self, logical_rect: QRect) -> QRect:
        """Map widget logical coordinates to the captured pixmap's pixel space."""
        if self._shot.isNull():
            return logical_rect
        x_scale = self._shot.width() / max(1, self.width())
        y_scale = self._shot.height() / max(1, self.height())
        return QRect(
            int(logical_rect.x() * x_scale),
            int(logical_rect.y() * y_scale),
            max(1, int(logical_rect.width() * x_scale)),
            max(1, int(logical_rect.height() * y_scale)),
        )


def install_screenshot_shortcut(parent, callback, sequence: str = "Ctrl+Shift+S") -> QShortcut:
    shortcut = QShortcut(QKeySequence(normalize_shortcut(sequence)), parent)
    shortcut.setContext(Qt.ApplicationShortcut)
    shortcut.activated.connect(callback)
    return shortcut
