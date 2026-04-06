# [[file:testing.org::*SDK test fixtures][SDK test fixtures:2]]
import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from dagger import dag

ROOT = Path(__file__).resolve().parents[1]
SPECS_DIR = Path(__file__).parent / "specs"
EXPECTED_DIR = Path(__file__).parent / "expected"
spec_files = sorted(SPECS_DIR.glob("*.yml")) if SPECS_DIR.exists() else []


def _kebab_to_snake(name):
    """Convert dagger CLI kebab-case name to Python snake_case method name.

    Dagger splits on digit boundaries (python3 → python-3), so simple
    replace("-", "_") doesn't work. First collapse digit boundaries
    (python-3 → python3), then replace remaining hyphens with underscores.
    """
    return re.sub(r"-(\d)", r"\1", name).replace("-", "_")


def resolve_vars(s, tmp_path):
    """Replace $TMP/${TMP} and $ROOT/${ROOT} in a string."""
    s = s.replace("${TMP}", str(tmp_path)).replace("$TMP", str(tmp_path))
    s = s.replace("${ROOT}", str(ROOT)).replace("$ROOT", str(ROOT))
    return s


def run_shell(cmd, tmp_path):
    """Run a shell command and return its stdout."""
    env = {**os.environ, "TMP": str(tmp_path), "ROOT": str(ROOT)}
    env["PATH"] = str(ROOT / "tests") + ":" + env.get("PATH", "")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )
    return result.stdout.rstrip("\n")


async def run_spec(lib, spec, tmp_path):
    """Interpret a YAML spec dict as dagger SDK calls."""
    if "shell" in spec:
        return run_shell(spec["shell"], tmp_path)

    func_name = _kebab_to_snake(spec["func"])
    kwargs = {k.replace("-", "_"): v for k, v in spec.get("args", {}).items()}
    obj = getattr(lib, func_name)(**kwargs)

    for step in spec.get("chain", []):
        if step == "stdout":
            return (await obj.stdout()).rstrip("\n")
        if not isinstance(step, dict):
            continue
        if "with-exec" in step:
            obj = obj.with_exec(step["with-exec"])
        elif "file" in step:
            obj = obj.file(step["file"])
        elif "export" in step:
            path = resolve_vars(step["export"], tmp_path)
            os.makedirs(Path(path).parent, exist_ok=True)
            await obj.export(path)
            if "post" in spec:
                return run_shell(resolve_vars(spec["post"], tmp_path), tmp_path)
            return ""
        elif "with-file" in step:
            wf = step["with-file"]
            source = resolve_vars(wf["source"], tmp_path)
            file_obj = dag.file(Path(source).name, Path(source).read_text())
            obj = obj.with_file(wf["path"], file_obj)
    return ""


@pytest.mark.parametrize(
    "spec_file",
    spec_files,
    ids=[s.stem for s in spec_files],
)
async def test_spec(lib, tmp_path, spec_file):
    spec = yaml.safe_load(spec_file.read_text())
    expected_file = EXPECTED_DIR / spec_file.stem
    expected = expected_file.read_text() if expected_file.exists() else ""
    result = await run_spec(lib, spec, tmp_path)
    assert result == expected.rstrip("\n"), (
        f"spec {spec_file.stem}: got {result!r}, expected {expected.rstrip(chr(10))!r}"
    )


# SDK test fixtures:2 ends here
