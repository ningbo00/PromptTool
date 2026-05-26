from dataclasses import dataclass, field


@dataclass(frozen=True)
class Prompt:
    title: str = ""
    content: str = ""

    def __post_init__(self):
        object.__setattr__(self, "title", str(self.title).strip())
        object.__setattr__(self, "content", str(self.content).strip())

    def display_label(self, fallback_length: int = 20) -> str:
        if self.title:
            return self.title
        if len(self.content) > fallback_length:
            return f"{self.content[:fallback_length]}..."
        return self.content

    def to_dict(self) -> dict:
        return {"title": self.title, "content": self.content}


@dataclass
class PromptLibrary:
    prompts: list[Prompt] = field(default_factory=list)

    def __post_init__(self):
        self.prompts = [self._coerce_prompt(prompt) for prompt in self.prompts]

    def search(self, query: str) -> list[int]:
        normalized = query.strip().lower()
        if not normalized:
            return list(range(len(self.prompts)))
        return [
            index
            for index, prompt in enumerate(self.prompts)
            if normalized in prompt.title.lower()
            or normalized in prompt.content.lower()
        ]

    def add_prompt(self, title: str = "新 Prompt", content: str = "") -> int:
        self.prompts.append(Prompt(title, content))
        return len(self.prompts) - 1

    def update_prompt(self, index: int, title: str, content: str) -> None:
        self._validate_index(index)
        normalized_title = str(title).strip() or "未命名"
        self.prompts[index] = Prompt(normalized_title, content)

    def delete_prompt(self, index: int) -> Prompt:
        self._validate_index(index)
        return self.prompts.pop(index)

    def move_prompt(self, index: int, direction: int) -> int:
        self._validate_index(index)
        target_index = index + direction
        if not 0 <= target_index < len(self.prompts):
            return index
        self.prompts[index], self.prompts[target_index] = (
            self.prompts[target_index],
            self.prompts[index],
        )
        return target_index

    def to_dicts(self) -> list[dict]:
        return [prompt.to_dict() for prompt in self.prompts]

    def _validate_index(self, index: int) -> None:
        if not 0 <= index < len(self.prompts):
            raise IndexError(f"Prompt index out of range: {index}")

    @staticmethod
    def _coerce_prompt(prompt) -> Prompt:
        if isinstance(prompt, Prompt):
            return prompt
        if isinstance(prompt, dict):
            return Prompt(prompt.get("title", ""), prompt.get("content", ""))
        raise TypeError(f"Unsupported prompt type: {type(prompt)!r}")


@dataclass
class PromptSelection:
    checked_indices: set[int] = field(default_factory=set)

    def toggle(self, index: int) -> None:
        if index in self.checked_indices:
            self.checked_indices.remove(index)
        else:
            self.checked_indices.add(index)

    def select_all(self, library: PromptLibrary) -> None:
        self.checked_indices = set(range(len(library.prompts)))

    def clear(self) -> None:
        self.checked_indices.clear()

    def reindex_after_delete(self, deleted_index: int) -> None:
        updated = set()
        for index in self.checked_indices:
            if index == deleted_index:
                continue
            updated.add(index - 1 if index > deleted_index else index)
        self.checked_indices = updated

    def swap_indices(self, first_index: int, second_index: int) -> None:
        updated = set()
        for index in self.checked_indices:
            if index == first_index:
                updated.add(second_index)
            elif index == second_index:
                updated.add(first_index)
            else:
                updated.add(index)
        self.checked_indices = updated

    def join_checked_contents(self, library: PromptLibrary) -> str:
        return "\n\n".join(
            library.prompts[index].content
            for index in range(len(library.prompts))
            if index in self.checked_indices
        )
