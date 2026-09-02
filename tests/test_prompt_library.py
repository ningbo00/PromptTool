from core.domain.prompt_library import Prompt, PromptLibrary, PromptSelection


def test_prompt_normalizes_title_and_content():
    prompt = Prompt(title="  Title  ", content="  Body  ", shortcut=" Ctrl+Alt+1 ")

    assert prompt.title == "Title"
    assert prompt.content == "Body"
    assert prompt.shortcut == "Ctrl+Alt+1"


def test_prompt_to_dict_omits_empty_shortcut_and_keeps_configured_shortcut():
    assert Prompt("A", "first").to_dict() == {"title": "A", "content": "first"}
    assert Prompt("A", "first", "Ctrl+Alt+1").to_dict() == {
        "title": "A",
        "content": "first",
        "shortcut": "Ctrl+Alt+1",
    }


def test_prompt_display_label_prefers_title():
    prompt = Prompt(title="Camera", content="long prompt content")

    assert prompt.display_label() == "Camera"


def test_prompt_display_label_falls_back_to_content_preview():
    prompt = Prompt(title="", content="abcdefghijklmnopqrstuvwxyz")

    assert prompt.display_label() == "abcdefghijklmnopqrst..."


def test_library_search_matches_title_or_content_case_insensitive():
    library = PromptLibrary(
        [
            Prompt("Portrait", "soft light"),
            Prompt("Landscape", "mountain sunset"),
            Prompt("Motion", "fast camera move"),
        ]
    )

    assert library.search("SUN") == [1]
    assert library.search("trait") == [0]
    assert library.search("camera") == [2]


def test_library_search_treats_placeholder_as_empty_query():
    library = PromptLibrary([Prompt("A", ""), Prompt("B", "")])

    assert library.search("搜索...") == [0, 1]
    assert library.search("Search") == [0, 1]


def test_library_add_save_update_and_delete_prompt():
    library = PromptLibrary()

    idx = library.add_prompt(title=" New ", content=" Body ")
    library.update_prompt(idx, title="", content="Updated")
    deleted = library.delete_prompt(idx)

    assert idx == 0
    assert deleted == Prompt("未命名", "Updated")
    assert library.to_dicts() == []


def test_library_update_empty_title_defaults_to_unnamed():
    library = PromptLibrary([Prompt("Old", "Body")])

    library.update_prompt(0, title="   ", content="New Body")

    assert library.prompts[0] == Prompt("未命名", "New Body")


def test_library_update_preserves_or_replaces_shortcut():
    library = PromptLibrary([Prompt("Old", "Body", "Ctrl+Alt+1")])

    library.update_prompt(0, title="New", content="Body 2")
    assert library.prompts[0] == Prompt("New", "Body 2", "Ctrl+Alt+1")

    library.update_prompt(0, title="New", content="Body 3", shortcut="F8")
    assert library.prompts[0] == Prompt("New", "Body 3", "F8")


def test_library_move_swaps_prompts_and_returns_new_index():
    library = PromptLibrary([Prompt("A", ""), Prompt("B", ""), Prompt("C", "")])

    new_index = library.move_prompt(1, -1)

    assert new_index == 0
    assert [prompt.title for prompt in library.prompts] == ["B", "A", "C"]


def test_library_move_at_boundary_keeps_order_and_index():
    library = PromptLibrary([Prompt("A", ""), Prompt("B", "")])

    new_index = library.move_prompt(0, -1)

    assert new_index == 0
    assert [prompt.title for prompt in library.prompts] == ["A", "B"]


def test_selection_toggle_select_all_clear_and_join_checked_prompts():
    library = PromptLibrary(
        [
            Prompt("A", "first"),
            Prompt("B", "second"),
            Prompt("C", "third"),
        ]
    )
    selection = PromptSelection()

    selection.toggle(2)
    selection.toggle(0)
    copied = selection.join_checked_contents(library)
    selection.select_all(library)
    selection.clear()

    assert copied == "first\n\nthird"
    assert selection.checked_indices == set()


def test_selection_join_checked_contents_returns_empty_when_none_checked():
    library = PromptLibrary([Prompt("A", "first")])
    selection = PromptSelection()

    assert selection.join_checked_contents(library) == ""


def test_selection_reindexes_after_delete():
    selection = PromptSelection(checked_indices={0, 2, 3})

    selection.reindex_after_delete(2)

    assert selection.checked_indices == {0, 2}


def test_selection_swaps_checked_indices_after_move():
    selection = PromptSelection(checked_indices={0, 2})

    selection.swap_indices(1, 2)

    assert selection.checked_indices == {0, 1}
