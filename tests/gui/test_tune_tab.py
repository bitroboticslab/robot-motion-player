from motion_player.gui.tabs.tune_tab import build_tune_tab_config


def test_tune_tab_exposes_numeric_inputs_with_units() -> None:
    cfg = build_tune_tab_config(language="en")
    assert "position_unit" in cfg.fields
    assert "angle_unit" in cfg.fields
    assert "step_position" in cfg.fields
    assert "step_angle" in cfg.fields
