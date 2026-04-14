from __future__ import annotations

from motion_player.gui.tabs.layout_spec import TAB_CONTROL_KEYS


def test_every_core_control_belongs_to_exactly_one_tab() -> None:
    all_keys: list[str] = []
    for keys in TAB_CONTROL_KEYS.values():
        all_keys.extend(keys)
    assert len(all_keys) == len(set(all_keys))


def test_play_controls_only_live_in_play_tab() -> None:
    play_expected = {
        "play_pause",
        "reset",
        "prev_1",
        "next_1",
        "speed_slider",
        "frame_slider",
        "clip_slider",
    }
    assert play_expected.issubset(set(TAB_CONTROL_KEYS["play"]))
    for tab_id, keys in TAB_CONTROL_KEYS.items():
        if tab_id == "play":
            continue
        assert play_expected.isdisjoint(set(keys))
