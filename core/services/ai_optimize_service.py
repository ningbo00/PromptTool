import re
from dataclasses import dataclass

from core.services.ai_optimize_actions import build_ai_optimize_messages


class AIOptimizeValidationError(ValueError):
    pass


@dataclass(frozen=True)
class AIOptimizeRequest:
    action: str
    messages: list[dict]
    temperature: float
    history_label: str


class AIOptimizeService:
    _TEMPERATURES = {
        "score": 0.3,
        "extract_keywords": 0.2,
        "recommend_negative": 0.3,
        "compliance_check": 0.2,
    }

    _HISTORY_LABELS = {
        "zh_to_en": "中文→英文",
        "generate_variants": "生成3变体",
        "score": "AI评分",
        "extract_keywords": "提取关键词",
        "recommend_negative": "推荐负面词",
        "compliance_check": "合规检验",
    }

    def __init__(self, custom_direction_label: str = "自定义指令（在下方输入）"):
        self.custom_direction_label = custom_direction_label

    def prepare_action(
        self,
        action: str,
        original: str,
        direction: str = "",
        custom_direction: str = "",
        length: str = "中等",
    ) -> AIOptimizeRequest:
        original = original.strip()
        if not original:
            raise AIOptimizeValidationError("原始 Prompt 为空")

        resolved_direction = self.resolve_direction(direction, custom_direction)
        messages = build_ai_optimize_messages(
            action=action,
            original=original,
            direction=resolved_direction,
            length=length,
        )
        return AIOptimizeRequest(
            action=action,
            messages=messages,
            temperature=self._TEMPERATURES.get(action, 0.7),
            history_label=self._history_label(action, resolved_direction),
        )

    def resolve_direction(self, direction: str, custom_direction: str = "") -> str:
        if direction == self.custom_direction_label:
            custom_direction = custom_direction.strip()
            if not custom_direction:
                raise AIOptimizeValidationError("请在自定义指令栏输入具体指令")
            return custom_direction
        return direction.strip()

    def parse_variants(self, text: str) -> list[str]:
        patterns = [
            r"\[变体(\d)\]",
            r"【变体(\d)】",
            r"\*\*变体(\d)\*\*",
            r"变体(\d)[：:．.]",
            r"\[Variant\s*(\d)\]",
            r"Variant\s*(\d)[：:．.]",
        ]

        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if len(matches) >= 2:
                parts = []
                for index, match in enumerate(matches):
                    start = match.end()
                    end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                    content = text[start:end].strip()
                    if content:
                        parts.append(content)
                if len(parts) >= 2:
                    return parts

        numbered = re.split(r"\n?\s*[123][.、)]\s*", text)
        parts = [part.strip() for part in numbered if part.strip()]
        if len(parts) >= 3:
            return parts[:3]
        return []

    def parse_keywords(self, text: str) -> list[str]:
        return [keyword.strip() for keyword in text.split(",") if keyword.strip()]

    def _history_label(self, action: str, direction: str) -> str:
        if action == "optimize_current":
            return direction
        return self._HISTORY_LABELS.get(action, action)
