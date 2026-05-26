from typing import Protocol

from core.domain.prompt_library import Prompt, PromptLibrary


class PromptStore(Protocol):
    def load(self) -> PromptLibrary:
        ...

    def save(self, prompts: list[Prompt]) -> None:
        ...
