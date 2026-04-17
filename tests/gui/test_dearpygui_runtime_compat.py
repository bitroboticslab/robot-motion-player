"""Runtime compatibility tests for DearPyGui panel wiring."""

from __future__ import annotations

import pytest

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


class _FakeDPGPartialFontFailure:
    mvFontRangeHint_Chinese_Full = 99

    def __init__(self) -> None:
        self.calls = 0
        self.bound_font = None

    def font_registry(self):
        return _Ctx()

    def add_font(self, _path: str, _size: int):
        self.calls += 1
        if self.calls == 1:
            return 321
        raise RuntimeError("partial failure")

    def add_font_range_hint(self, _hint: int, parent=None):
        del _hint, parent
        return None

    def bind_font(self, font):
        self.bound_font = font


def test_install_fonts_uses_font_parent_for_range_hint(monkeypatch, tmp_path) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    font_file = tmp_path / "NotoSansCJK-Regular.ttc"
    font_file.write_bytes(b"font")
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [font_file])

    fake = _FakeDPGFontOK()
    panel._install_fonts(fake)

    assert fake.range_hint_parent == 123
    assert fake.bound_font == 123


def test_install_fonts_registers_all_size_variants(monkeypatch, tmp_path) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    font_file = tmp_path / "NotoSansCJK-Regular.ttc"
    font_file.write_bytes(b"font")
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [font_file])

    fake = _FakeDPGFontOK()
    panel._install_fonts(fake)

    assert set(panel._font_handles.keys()) == {"small", "medium", "large", "xlarge"}


def test_install_fonts_uses_platform_fallback_when_no_cjk(monkeypatch, tmp_path) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    latin = tmp_path / "DejaVuSans.ttf"
    latin.write_bytes(b"font")
    monkeypatch.delenv("RMP_GUI_FONT", raising=False)
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [])
    monkeypatch.setattr(panel, "_default_ui_font_candidates", lambda: [latin])

    fake = _FakeDPGFontOK()
    panel._install_fonts(fake)

    assert set(panel._font_handles.keys()) == {"small", "medium", "large", "xlarge"}


def test_install_fonts_leaves_no_fonts_when_resolution_fails(monkeypatch) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    monkeypatch.delenv("RMP_GUI_FONT", raising=False)
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [])
    monkeypatch.setattr(panel, "_default_ui_font_candidates", lambda: [])

    fake = _FakeDPGFontOK()
    with pytest.raises(RuntimeError):
        panel._install_fonts(fake)


def test_make_dpg_callback_accepts_three_args() -> None:
    calls: list[str] = []
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")

    cb = panel._make_dpg_callback(lambda: calls.append("ok"))
    cb("sender", 1.0, {"x": 1})
    panel._drain_ui_commands()

    assert calls == ["ok"]


def test_panel_drain_order_processes_callbacks_then_ui_commands() -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    events: list[str] = []
    panel._dpg = type(
        "_FakeDpg",
        (),
        {
            "get_callback_queue": staticmethod(lambda: [(lambda: events.append("dpg_cb"), (), {})]),
            "run_callbacks": staticmethod(
                lambda jobs: [fn(*args, **kwargs) for fn, args, kwargs in jobs]
            ),
        },
    )()
    panel._enqueue_ui_command(lambda: events.append("ui_cmd"))

    panel._drain_dpg_callback_queue()
    panel._drain_ui_commands()

    assert events == ["dpg_cb", "ui_cmd"]


def test_install_fonts_raises_when_all_size_hints_fail(monkeypatch, tmp_path) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    font_file = tmp_path / "NotoSansCJK-Regular.ttc"
    font_file.write_bytes(b"font")
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [font_file])

    fake = _FakeDPGHintRaises()
    with pytest.raises(RuntimeError):
        panel._install_fonts(fake)


def test_install_fonts_keeps_successful_sizes_when_later_sizes_fail(monkeypatch, tmp_path) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    font_file = tmp_path / "NotoSansCJK-Regular.ttc"
    font_file.write_bytes(b"font")
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [font_file])

    fake = _FakeDPGPartialFontFailure()
    panel._install_fonts(fake)

    assert panel._font_handles == {"small": 321}
    assert "medium" in panel._font_unavailable_reasons
    assert fake.bound_font == 321


def test_install_fonts_fallback_syncs_requested_key(monkeypatch, tmp_path) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    font_file = tmp_path / "NotoSansCJK-Regular.ttc"
    font_file.write_bytes(b"font")
    monkeypatch.setattr(panel, "_default_cjk_candidates", lambda: [font_file])

    fake = _FakeDPGPartialFontFailure()
    panel._install_fonts(fake)

    assert panel._font_size_key == "small"
    assert panel._font_requested_key == "small"


def test_run_process_entry_reports_failed_status_without_raising(monkeypatch) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")

    def _boom() -> None:
        raise RuntimeError("startup failure")

    monkeypatch.setattr(panel, "_run_blocking", _boom)
    statuses: list[str] = []

    rc = panel.run_process_entry(statuses.append)

    assert rc == 1
    assert statuses[0] == "starting"
    assert statuses[-1].startswith("failed:")


def test_run_process_entry_reports_stopped_on_clean_shutdown(monkeypatch) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    monkeypatch.setattr(panel, "_run_blocking", lambda: None)
    statuses: list[str] = []

    rc = panel.run_process_entry(statuses.append)

    assert rc == 0
    assert statuses == ["starting", "stopped"]


def test_run_process_entry_ignores_status_callback_errors(monkeypatch) -> None:
    panel = DearPyGuiPanel(controller=_DummyController(), title="Test")
    monkeypatch.setattr(panel, "_run_blocking", lambda: None)

    def _broken_status_cb(_message: str) -> None:
        raise RuntimeError("callback failure")

    rc = panel.run_process_entry(_broken_status_cb)
    assert rc == 0
