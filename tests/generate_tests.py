#!/usr/bin/env python3
"""Generate dagger call CLI commands from YAML test specs."""
import sys

import yaml


def spec_to_cli(spec: dict) -> str:
    """Convert a test spec dict to a dagger call command string.

    Handles: func+args+chain (stdout, export, file, with-exec, with-file)
    and shell-only specs.
    """
    if "shell" in spec:
        return spec["shell"]

    parts = ["dagger call", spec["func"]]

    for key, val in spec.get("args", {}).items():
        if isinstance(val, list):
            for item in val:
                parts.append(f"--{key}={item}")
        elif " " in str(val) or "'" in str(val) or "$" in str(val):
            parts.append(f'--{key}="{val}"')
        else:
            parts.append(f"--{key}={val}")

    for step in spec.get("chain", []):
        if step == "stdout":
            parts.append("stdout")
        elif isinstance(step, str) and step.startswith("export"):
            # bare "export" shouldn't happen — use dict form
            parts.append('export --path="$TMP/out"')
        elif isinstance(step, dict):
            if "with-exec" in step:
                args = ",".join(f'"{a}"' for a in step["with-exec"])
                parts.append(f"with-exec --args={args}")
            elif "export" in step:
                path = step["export"]
                parts.append(f'export --path="{path}"')
            elif "file" in step:
                path = step["file"]
                parts.append(f'file --path="{path}"')
            elif "with-file" in step:
                wf = step["with-file"]
                source = wf["source"]
                if "$" in source or " " in source:
                    source = f'"{source}"'
                parts.append(f'with-file --path={wf["path"]} --source={source}')

    cli = " ".join(parts)

    # Export commands redirect to /dev/null; post commands follow on next line
    if any(isinstance(s, dict) and "export" in s for s in spec.get("chain", [])):
        cli += " > /dev/null"

    if "post" in spec:
        cli += "\n" + spec["post"]

    return cli


if __name__ == "__main__":
    spec = yaml.safe_load(sys.stdin)
    print(spec_to_cli(spec))
