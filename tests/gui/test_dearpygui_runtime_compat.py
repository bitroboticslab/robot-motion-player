"""Runtime compatibility tests for DearPyGui panel wiring."""

from __future__ import annotations

from motion_player.gui.dearpygui_panel import DearPyGuiPanel


class _DummyController:
    pass


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeDPGFontOK:
    mvFontRangeHint_Chinese_Full = 99

    def __init__(self) -> None:
        self.range_hint_parent = None
        self.bound_font = None

    def font_registry(self):
        return _Ctx()

    def add_font(self, _path: str, _size: int):
        return 123

    def add_font_range_hint(self, _hint: int, parent=None):
        self.range_hint_parent = parent

    def bind_font(self, font):
        self.bound_font = font


class _FakeDPGHintRaises:
    mvFontRangeHint_Chinese_Full = 99

    def font_registry(self):
        return _Ctx()

    def add_font(self, _path: str, _size: int):
        return 123

    def add_font_range_hint(self, _hint: int, parent=None):
        raise RuntimeError("range hint failure")

    def bind_font(self, _font):
        return None


def test_install_fonts_uses_font_parent_for_range_hint(monkeypatch, tmp_path) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    font_file = tmp_path / "NotoSansCJK-Regular.ttc"
    font_file.write_bytes(b"font")
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [font_file])

    fake = _FakeDPGFontOK()
    panel._install_fonts(fake)

    assert fake.range_hint_parent == 123
    assert fake.bound_font == 123


def test_make_dpg_callback_accepts_three_args() -> None:
    calls: list[str] = []
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")

    cb = panel._make_dpg_callback(lambda: calls.append("ok"))
    cb("sender", 1.0, {"x": 1})

    assert calls == ["ok"]


def test_install_fonts_fail_open_when_hint_raises(monkeypatch, tmp_path) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    font_file = tmp_path / "NotoSansCJK-Regular.ttc"
    font_file.write_bytes(b"font")
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [font_file])

    fake = _FakeDPGHintRaises()
    panel._install_fonts(fake)
