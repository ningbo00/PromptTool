from dataclasses import dataclass


@dataclass(frozen=True)
class CameraBuilderStep:
    key: str
    title: str
    tabs: list[str]


@dataclass(frozen=True)
class CameraBuilderLayoutSpec:
    steps: list[CameraBuilderStep]

    @classmethod
    def default(cls) -> "CameraBuilderLayoutSpec":
        return cls(
            steps=[
                CameraBuilderStep("scene", "1. 场景", ["subject"]),
                CameraBuilderStep("style", "2. 风格", ["preset", "style", "filter", "extractor"]),
                CameraBuilderStep("camera", "3. 镜头", ["params", "camera"]),
                CameraBuilderStep("output", "4. 输出", ["detail"]),
            ]
        )

    def step(self, key: str) -> CameraBuilderStep:
        for step in self.steps:
            if step.key == key:
                return step
        raise KeyError(f"Unknown camera builder step: {key}")
