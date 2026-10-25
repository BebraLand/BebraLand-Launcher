from pathlib import Path


def test_windows_build_specs_do_not_use_upx() -> None:
    root = Path(__file__).resolve().parents[1]
    specs = sorted(root.glob("*.spec"))
    assert {"BebraLandLauncher.spec", "BebraLandUpdater.spec"} <= {spec.name for spec in specs}
    for spec in specs:
        assert "upx=True" not in spec.read_text(encoding="utf-8"), spec.name


if __name__ == "__main__":
    test_windows_build_specs_do_not_use_upx()
