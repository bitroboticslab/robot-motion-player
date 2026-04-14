from motion_player.cli.main import build_parser


def test_export_subcommand_exists() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "export",
            "--motion",
            "m.pkl",
            "--robot",
            "r.xml",
            "--output",
            "out.mp4",
        ]
    )
    assert args.command == "export"
    assert args.output == "out.mp4"
