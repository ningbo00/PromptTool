from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutSection:
    key: str
    title: str
    primary_actions: list[str]
    secondary_actions: list[str]


@dataclass(frozen=True)
class MainLayoutSpec:
    toolbar_actions: list[str]
    sections: list[LayoutSection]

    @classmethod
    def default(cls) -> "MainLayoutSpec":
        return cls(
            toolbar_actions=["topmost", "compact", "settings", "help"],
            sections=[
                LayoutSection(
                    key="library",
                    title="Prompt 库",
                    primary_actions=["new", "edit", "delete"],
                    secondary_actions=["move_up", "move_down", "copy_checked"],
                ),
                LayoutSection(
                    key="editor",
                    title="当前 Prompt",
                    primary_actions=["save", "copy"],
                    secondary_actions=[],
                ),
                LayoutSection(
                    key="tools",
                    title="工作流工具",
                    primary_actions=["ai_optimize", "builder"],
                    secondary_actions=["ai_settings", "help"],
                ),
            ],
        )

    def section(self, key: str) -> LayoutSection:
        for section in self.sections:
            if section.key == key:
                return section
        raise KeyError(f"Unknown layout section: {key}")
