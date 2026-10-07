"""WEBZ-NATIVE-001: wheel users receive every fixed world asset."""
import subprocess
import sys
import zipfile
from pathlib import Path


def test_webz_flat_assets_are_in_installed_wheel(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    wheel_dir = tmp_path / "wheel"
    wheel_dir.mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps",
         "--no-build-isolation", ".", "-w", str(wheel_dir)],
        cwd=root, capture_output=True, text=True, timeout=180, check=False,
    )
    assert result.returncode == 0, result.stdout[-1600:] + "\n" + result.stderr[-1600:]
    wheels = sorted(wheel_dir.glob("static_workbench-*.whl"))
    assert len(wheels) == 1
    expected = {
        "webz.html", "webz.js", "webz.css", "webz-world.js",
        "webz-voyage.mjs", "webz-storage.mjs", "webz-registry.json",
        "webz-sanctuary.json", "webz-orchard.json",
        "webz-sanctuary.html", "webz-orchard.html",
        "webz-parcel.js", "webz-fruit.json", "webz-spore.json",
        "webz-custody.js",
    }
    with zipfile.ZipFile(wheels[0]) as archive:
        members = set(archive.namelist())
    for name in sorted(expected):
        assert "static_workbench/web/" + name in members, (
            name + " missing from the installed Workbench wheel"
        )
