"""Version and OSS docs consistency checks."""

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def _project_version() -> str:
    pyproject = Path("pyproject.toml")
    if tomllib is not None:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return data["project"]["version"]
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.partition('"')[2].rpartition('"')[0]
    raise AssertionError("project version not found in pyproject.toml")


def test_version_markers_follow_project_version() -> None:
    project_version = _project_version()
    expected_dev_version = f"{project_version}.dev0"

    init_text = Path("motion_player/__init__.py").read_text(encoding="utf-8")
    cli_text = Path("motion_player/cli/main.py").read_text(encoding="utf-8")

    assert f'__version__ = "{expected_dev_version}"' in init_text
    assert f'return "{expected_dev_version}"' in cli_text


def test_v080_docs_align_with_font_size_release_behavior() -> None:
    quickstart_en = Path("docs/QUICKSTART_en.md").read_text(encoding="utf-8")
    quickstart_zh = Path("docs/QUICKSTART_zh.md").read_text(encoding="utf-8")
    ik_usage = Path("docs/IK_USAGE.md").read_text(encoding="utf-8")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert "## [0.8.0]" in changelog
    assert "--font-size" in changelog
    assert "RMP_GUI_FONT_SIZE" in changelog

    for text in (quickstart_en, quickstart_zh, ik_usage):
        assert "--font-size" in text
        assert "RMP_GUI_FONT_SIZE" in text


def test_readme_references_oss_docs_only() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "[English](README.md)" in readme
    assert "[中文](README_zh.md)" in readme
    assert "docs/QUICKSTART_en.md" in readme
    assert "docs/IK_USAGE.md" in readme
    assert "README_CN.md" not in readme
