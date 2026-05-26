from core.domain.prompt_library import Prompt
from core.services.prompt_service import PromptService


class InMemoryPromptStore:
    def __init__(self, prompts=None):
        self.prompts = list(prompts or [])
        self.saved_snapshots = []

    def load(self):
        from core.domain.prompt_library import PromptLibrary

        return PromptLibrary(self.prompts)

    def save(self, prompts):
        self.saved_snapshots.append(list(prompts))
        self.prompts = list(prompts)


def test_service_loads_library_from_store():
    service = PromptService(InMemoryPromptStore([Prompt("A", "first")]))

    assert service.library.prompts == [Prompt("A", "first")]


def test_service_adds_prompt_and_persists():
    store = InMemoryPromptStore()
    service = PromptService(store)

    index = service.add_prompt(" A ", " first ")

    assert index == 0
    assert service.library.prompts == [Prompt("A", "first")]
    assert store.saved_snapshots[-1] == [Prompt("A", "first")]


def test_service_updates_prompt_and_persists():
    store = InMemoryPromptStore([Prompt("A", "first")])
    service = PromptService(store)

    service.update_prompt(0, " ", "updated")

    assert service.library.prompts == [Prompt("未命名", "updated")]
    assert store.saved_snapshots[-1] == [Prompt("未命名", "updated")]


def test_service_deletes_prompt_reindexes_selection_and_persists():
    store = InMemoryPromptStore(
        [Prompt("A", "first"), Prompt("B", "second"), Prompt("C", "third")]
    )
    service = PromptService(store)
    service.selection.checked_indices = {0, 2}

    deleted = service.delete_prompt(1)

    assert deleted == Prompt("B", "second")
    assert service.library.prompts == [Prompt("A", "first"), Prompt("C", "third")]
    assert service.selection.checked_indices == {0, 1}
    assert store.saved_snapshots[-1] == service.library.prompts


def test_service_moves_prompt_updates_selection_and_persists():
    store = InMemoryPromptStore(
        [Prompt("A", "first"), Prompt("B", "second"), Prompt("C", "third")]
    )
    service = PromptService(store)
    service.selection.checked_indices = {0, 2}

    new_index = service.move_prompt(1, 1)

    assert new_index == 2
    assert service.library.prompts == [Prompt("A", "first"), Prompt("C", "third"), Prompt("B", "second")]
    assert service.selection.checked_indices == {0, 1}
    assert store.saved_snapshots[-1] == service.library.prompts


def test_service_move_boundary_does_not_persist():
    store = InMemoryPromptStore([Prompt("A", "first")])
    service = PromptService(store)

    new_index = service.move_prompt(0, -1)

    assert new_index == 0
    assert store.saved_snapshots == []


def test_service_selection_and_join_checked_contents():
    service = PromptService(
        InMemoryPromptStore([Prompt("A", "first"), Prompt("B", "second")])
    )

    service.toggle_checked(1)
    service.toggle_checked(0)

    assert service.join_checked_contents() == "first\n\nsecond"


def test_service_search_delegates_to_library():
    service = PromptService(
        InMemoryPromptStore([Prompt("A", "first"), Prompt("B", "second")])
    )

    assert service.search("second") == [1]


def test_service_exposes_library_status():
    service = PromptService(
        InMemoryPromptStore([Prompt("A", "first"), Prompt("B", "second")])
    )

    service.toggle_checked(1)

    assert service.status_summary(selected_index=0) == {
        "total": 2,
        "checked": 1,
        "selected": True,
        "selected_index": 0,
    }


def test_service_status_summary_marks_missing_selection():
    service = PromptService(InMemoryPromptStore([Prompt("A", "first")]))

    assert service.status_summary(selected_index=None) == {
        "total": 1,
        "checked": 0,
        "selected": False,
        "selected_index": None,
    }
