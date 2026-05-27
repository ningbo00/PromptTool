from pathlib import Path


def test_user_and_release_docs_exist_with_required_sections():
    user_guide = Path("docs/USER_GUIDE.md").read_text(encoding="utf-8")
    release = Path("docs/RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "快速启动" in user_guide
    assert "提示词生成器" in user_guide
    assert "AI 优化" in user_guide
    assert "打包命令" in release
    assert "GUI E2E" in release
    assert "PromptTool" in readme
