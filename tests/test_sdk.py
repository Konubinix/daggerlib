# [[file:testing.org::*Test fixtures][Test fixtures:1]]
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).parent


def _collect(commands_dir, cwd):
    """Collect (cmd_file, expected_dir, cwd) triples from a commands dir."""
    if not commands_dir.exists():
        return []
    expected_dir = commands_dir.parent / "expected"
    return [(f, expected_dir, cwd) for f in sorted(commands_dir.glob("*"))]


def _test_id(entry):
    cmd_file, _, cwd = entry
    if cwd == ROOT:
        return cmd_file.name
    return f"{cwd.name}/{cmd_file.name}"


lib_tests = _collect(TESTS_DIR / "commands", ROOT)
example_tests = [
    entry
    for example_dir in sorted(ROOT.glob("examples/*"))
    for entry in _collect(example_dir / "tests" / "commands", example_dir)
]
all_tests = lib_tests + example_tests


@pytest.mark.parametrize(
    "cmd_file,expected_dir,cwd",
    all_tests,
    ids=[_test_id(e) for e in all_tests],
)
def test_command(tmp_path, cmd_file, expected_dir, cwd):
    env = {**os.environ, "TMP": str(tmp_path), "ROOT": str(ROOT)}
    env["PATH"] = str(ROOT / "tests") + ":" + env.get("PATH", "")
    result = subprocess.run(
        ["bash", str(cmd_file)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )
    assert result.returncode == 0, (
        f"command {cmd_file.name} failed (exit {result.returncode}):\n{result.stderr}"
    )
    expected_file = expected_dir / cmd_file.name
    expected = expected_file.read_text().rstrip("\n") if expected_file.exists() else ""
    assert result.stdout.rstrip("\n") == expected, (
        f"{cmd_file.name}: got {result.stdout.rstrip(chr(10))!r}, expected {expected!r}"
    )


# Test fixtures:1 ends here
