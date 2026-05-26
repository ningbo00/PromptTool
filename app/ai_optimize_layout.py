from dataclasses import dataclass


@dataclass(frozen=True)
class AIOptimizeLayoutSpec:
    panels: list[str]
    action_groups: dict[str, list[str]]

    @classmethod
    def default(cls) -> "AIOptimizeLayoutSpec":
        return cls(
            panels=["source", "instruction", "result", "insights"],
            action_groups={
                "primary": [
                    "optimize_current",
                    "zh_to_en",
                    "generate_variants",
                ],
                "advanced": [
                    "score",
                    "extract_keywords",
                    "recommend_negative",
                    "compliance_check",
                ],
                "result": [
                    "apply_to_current",
                    "save_as_new",
                    "copy_result",
                ],
            },
        )

    def action_group(self, name: str) -> list[str]:
        return self.action_groups[name]
