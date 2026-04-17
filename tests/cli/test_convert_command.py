"""CLI conversion command routing tests."""

from __future__ import annotations

import argparse

from motion_player.cli.main import _cmd_convert


def test_convert_xml_input_to_xml_prints_already_xml_hint(capsys, tmp_path) -> None:
    xml_in = tmp_path / "robot.xml"
    xml_out = tmp_path / "robot_out.xml"
    xml_in.write_text("<mujoco/>", encoding="utf-8")

    rc = _cmd_convert(argparse.Namespace(input=str(xml_in), output=str(xml_out)))
    captured = capsys.readouterr()

    assert rc == 0
    assert "already XML" in captured.out


def test_convert_xml_to_urdf_reports_unsupported_direction(capsys, tmp_path) -> None:
    xml_in = tmp_path / "robot.xml"
    urdf_out = tmp_path / "robot.urdf"
    xml_in.write_text("<mujoco/>", encoding="utf-8")

    rc = _cmd_convert(argparse.Namespace(input=str(xml_in), output=str(urdf_out)))
    captured = capsys.readouterr()

    assert rc == 1
    assert "XML->URDF" in captured.err


def test_convert_urdf_input_to_urdf_prints_already_urdf_hint(capsys, tmp_path) -> None:
    urdf_in = tmp_path / "robot.urdf"
    urdf_out = tmp_path / "robot_out.urdf"
    urdf_in.write_text("<robot/>", encoding="utf-8")

    rc = _cmd_convert(argparse.Namespace(input=str(urdf_in), output=str(urdf_out)))
    captured = capsys.readouterr()

    assert rc == 0
    assert "already URDF" in captured.out


def test_convert_xml_to_urdf_uses_external_backend_when_available(
    monkeypatch, capsys, tmp_path
) -> None:
    xml_in = tmp_path / "robot.xml"
    urdf_out = tmp_path / "robot.urdf"
    xml_in.write_text("<mujoco/>", encoding="utf-8")

    def _fake_convert_model(*, input_path, output_path):
        assert str(input_path).endswith(".xml")
        assert str(output_path).endswith(".urdf")
        return 0, "Converted", ""

    monkeypatch.setattr("motion_player.core.convert.router.convert_model", _fake_convert_model)

    rc = _cmd_convert(argparse.Namespace(input=str(xml_in), output=str(urdf_out)))
    captured = capsys.readouterr()

    assert rc == 0
    assert "Converted" in captured.out
