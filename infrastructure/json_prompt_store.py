import json
from pathlib import Path

from core.domain.prompt_library import Prompt, PromptLibrary


class JsonPromptStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> PromptLibrary:
        if not self.path.exists():
            return PromptLibrary()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return PromptLibrary()
        if not isinstance(data, list):
            return PromptLibrary()

        prompts = []
        for item in data:
            if not isinstance(item, dict):
                continue
            prompt = Prompt(item.get("title", ""), item.get("content", ""), item.get("shortcut", ""))
            if prompt.title or prompt.content:
                prompts.append(prompt)
        return PromptLibrary(prompts)

    def save(self, prompts: list[Prompt]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [prompt.to_dict() for prompt in prompts]
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
