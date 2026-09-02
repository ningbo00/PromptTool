from core.domain.prompt_library import Prompt, PromptLibrary, PromptSelection
from core.ports.prompt_store import PromptStore


class PromptService:
    def __init__(self, store: PromptStore):
        self.store = store
        self.library = store.load()
        self.selection = PromptSelection()

    @property
    def prompts(self) -> list[Prompt]:
        return self.library.prompts

    @property
    def checked_indices(self) -> set[int]:
        return self.selection.checked_indices

    def search(self, query: str) -> list[int]:
        return self.library.search(query)

    def add_prompt(self, title: str = "新 Prompt", content: str = "", shortcut: str = "") -> int:
        index = self.library.add_prompt(title, content, shortcut)
        self._persist()
        return index

    def update_prompt(self, index: int, title: str, content: str, shortcut: str | None = None) -> None:
        self.library.update_prompt(index, title, content, shortcut)
        self._persist()

    def delete_prompt(self, index: int) -> Prompt:
        deleted = self.library.delete_prompt(index)
        self.selection.reindex_after_delete(index)
        self._persist()
        return deleted

    def move_prompt(self, index: int, direction: int) -> int:
        new_index = self.library.move_prompt(index, direction)
        if new_index != index:
            self.selection.swap_indices(index, new_index)
            self._persist()
        return new_index

    def toggle_checked(self, index: int) -> None:
        self.selection.toggle(index)

    def select_all(self) -> None:
        self.selection.select_all(self.library)

    def clear_checked(self) -> None:
        self.selection.clear()

    def join_checked_contents(self) -> str:
        return self.selection.join_checked_contents(self.library)

    def status_summary(self, selected_index: int | None) -> dict:
        return {
            "total": len(self.library.prompts),
            "checked": len(self.selection.checked_indices),
            "selected": selected_index is not None,
            "selected_index": selected_index,
        }

    def action_state(self, selected_index: int | None) -> dict:
        total = len(self.library.prompts)
        has_selection = selected_index is not None and 0 <= selected_index < total
        return {
            "can_edit": has_selection,
            "can_delete": has_selection,
            "can_move_up": has_selection and selected_index > 0,
            "can_move_down": has_selection and selected_index < total - 1,
            "can_copy_checked": bool(self.selection.checked_indices),
            "can_ai_optimize": has_selection,
        }

    def _persist(self) -> None:
        self.store.save(self.library.prompts)
