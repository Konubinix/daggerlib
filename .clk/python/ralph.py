# [[file:../../src/ralph.org::*clk commands][clk commands:1]]
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ralph orchestrator CLI commands."""

import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import click

from clk.config import config
from clk.decorators import argument, command, group, option
from clk.log import get_logger

LOGGER = get_logger(__name__)

CONSUL_KEY_DEFAULT = "ralph/dagger/status"


@group()
def ralph():
    "Ralph orchestrator commands"


@ralph.command()
@option(
    "--max-iterations", type=int, default=50, help="Maximum number of ralph iterations"
)
@option(
    "--output-dir", default="ralph-output", help="Output directory for the artifact"
)
@option(
    "--credentials",
    type=click.Path(exists=True),
    default=os.path.expanduser("~/.claude/.credentials.json"),
    help="Path to claude code credentials",
)
@option(
    "--consul-key", default=CONSUL_KEY_DEFAULT, help="Consul KV key for stop signaling"
)
def run(max_iterations, output_dir, credentials, consul_key):
    "Run ralph orchestrator in a dagger container"
    project = config.project
    consul_addr = os.environ.get("CONSUL_HTTP_ADDR", "")
    runner_host = os.environ.get("_EXPERIMENTAL_DAGGER_RUNNER_HOST", "")

    ralph_args = f"run --max-iterations {max_iterations}"
    ralph_args += " -p 'Follow the instructions in ralph.yml hats'"

    dagger_args = [
        "call",
        "ralph",
        "--claude-credentials",
        f"file:{credentials}",
        "--extra-packages",
        "emacs-nox",
        "--extra-packages",
        "curl",
        "--extra-packages",
        "xz-utils",
        "--ralph-args",
        ralph_args,
    ]

    if runner_host:
        dagger_args += ["--dagger-runner-host", runner_host]
    if consul_addr:
        dagger_args += ["--consul-addr", consul_addr, "--consul-key", consul_key]

    ralph_yml = Path(project) / "src" / "ralph.yml"
    if ralph_yml.exists():
        dagger_args += ["--ralph-yml", str(ralph_yml)]
    todo_org = Path(project) / "todo.org"
    if todo_org.exists():
        dagger_args += ["--todo-org", str(todo_org)]

    pid_file = Path(project) / ".ralph-pid"
    log_file = Path(project) / ".ralph-log"

    def cleanup():
        pid_file.unlink(missing_ok=True)
        if consul_addr:
            subprocess.run(["consul", "kv", "delete", consul_key], capture_output=True)
            subprocess.run(
                ["consul", "kv", "delete", f"{consul_key}/log-level"],
                capture_output=True,
            )

    def handle_signal(signum, frame):
        cleanup()
        sys.exit(130)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if consul_addr:
        print(f"[ralph.run] setting consul key '{consul_key}' to 'running'")
        subprocess.run(
            ["consul", "kv", "put", consul_key, "running"],
            capture_output=True,
        )
        subprocess.run(
            ["consul", "kv", "put", f"{consul_key}/log-level", "normal"],
            capture_output=True,
        )
    else:
        print("[ralph.run] CONSUL_HTTP_ADDR not set, stop signaling disabled")

    print(f"[ralph.run] starting dagger (output-dir={output_dir}, log={log_file})...")
    pid_file.write_text(str(os.getpid()))

    try:
        dagger_cmd = (
            ["dagger", "--progress=plain"]
            + dagger_args
            + ["export", "--path", output_dir]
        )
        dagger_proc = subprocess.Popen(
            dagger_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=project,
        )
        filter_proc = subprocess.Popen(
            [sys.executable, str(Path(project) / "tests" / "ralph-log-filter")],
            stdin=subprocess.PIPE,
        )
        with open(log_file, "wb") as lf:
            for chunk in iter(lambda: dagger_proc.stdout.read(4096), b""):
                lf.write(chunk)
                filter_proc.stdin.write(chunk)
                filter_proc.stdin.flush()
        filter_proc.stdin.close()
        filter_proc.wait()
        rc = dagger_proc.wait()
        if rc == 0:
            print("[ralph.run] dagger completed successfully")
        else:
            print(f"[ralph.run] dagger exited with code {rc}")
    finally:
        cleanup()


@ralph.command()
@option(
    "--consul-key", default=CONSUL_KEY_DEFAULT, help="Consul KV key for stop signaling"
)
def stop(consul_key):
    "Stop a running ralph via Consul and wait for results to be exported"
    consul_addr = os.environ.get("CONSUL_HTTP_ADDR", "")
    if not consul_addr:
        raise click.ClickException("CONSUL_HTTP_ADDR is not set")

    project = config.project
    pid_file = Path(project) / ".ralph-pid"

    result = subprocess.run(
        ["consul", "kv", "get", consul_key], capture_output=True, text=True
    )
    status = result.stdout.strip() if result.returncode == 0 else ""
    print(f"[ralph.stop] consul key '{consul_key}' = '{status or 'empty'}'")
    if status != "running":
        raise click.ClickException("no running ralph found")

    print(f"[ralph.stop] writing 'stop' to consul key '{consul_key}'...")
    subprocess.run(["consul", "kv", "put", consul_key, "stop"], capture_output=True)

    if pid_file.exists():
        pid = pid_file.read_text().strip()
        print(f"[ralph.stop] waiting for dagger (PID {pid}) to finish exporting...")
        subprocess.run(
            ["tail", f"--pid={pid}", "-f", "/dev/null"],
            capture_output=True,
        )
        print("[ralph.stop] dagger process finished")
    else:
        print("[ralph.stop] no .ralph-pid file, cannot wait for dagger")

    print("[ralph.stop] done")


@ralph.command()
@option(
    "--consul-key", default=CONSUL_KEY_DEFAULT, help="Consul KV key for stop signaling"
)
@argument(
    "level",
    type=click.Choice(["normal", "think", "verbose", "json", "show"]),
    default="show",
    help="Log level. Omit to show current level.",
)
def log_level(consul_key, level):
    """Change the verbosity of a running ralph's output

    Levels:
      normal   filtered, categorized output (default)
      think    normal + claude thinking content
      verbose  show every line, truncated
      json     show every line raw"""
    consul_addr = os.environ.get("CONSUL_HTTP_ADDR", "")
    if not consul_addr:
        raise click.ClickException("CONSUL_HTTP_ADDR is not set")

    if level == "show":
        result = subprocess.run(
            ["consul", "kv", "get", f"{consul_key}/log-level"],
            capture_output=True,
            text=True,
        )
        print(result.stdout.strip() if result.returncode == 0 else "normal")
        return

    subprocess.run(
        ["consul", "kv", "put", f"{consul_key}/log-level", level],
        capture_output=True,
    )
    print(f"[ralph.log-level] set to '{level}'")


@ralph.command()
@option(
    "--output-dir", default="ralph-output", help="Output directory for the artifact"
)
def gather(output_dir):
    "Apply patches generated by a ralph run to the current branch"
    project = Path(config.project)
    patch_dir = project / output_dir / "patches"

    if not patch_dir.is_dir():
        raise click.ClickException(f"patch directory '{patch_dir}' not found")

    patches = sorted(patch_dir.glob("*.patch"))
    if not patches:
        print(f"No patches to apply in '{patch_dir}'")
        return

    # Back up untracked files that patches may create
    backed_up = []
    for p in patches:
        for line in p.read_text().splitlines():
            if line.startswith("+++ b/"):
                f = project / line[6:]
                if f.exists():
                    result = subprocess.run(
                        ["git", "ls-files", "--error-unmatch", str(f)],
                        capture_output=True,
                        cwd=project,
                    )
                    if result.returncode != 0:
                        shutil.move(str(f), f"{f}.ralph-backup")
                        backed_up.append(f)

    print(f"Applying {len(patches)} patch(es) from '{patch_dir}':")
    for p in patches:
        print(f"  {p.name}")

    result = subprocess.run(["git", "am"] + [str(p) for p in patches], cwd=project)
    if result.returncode != 0:
        for f in backed_up:
            backup = Path(f"{f}.ralph-backup")
            if backup.exists():
                shutil.move(str(backup), str(f))
        sys.exit(1)

    for f in backed_up:
        Path(f"{f}.ralph-backup").unlink(missing_ok=True)

    todo_src = project / output_dir / "todo.org"
    if todo_src.exists():
        shutil.copy2(str(todo_src), str(project / "todo.org"))
        print(f"Restored todo.org from {output_dir}/")


@ralph.command()
@option(
    "--log-file",
    type=click.Path(exists=True),
    default=None,
    help="Path to ralph log file (default: .ralph-log in project)",
)
@option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output fixture path (default: tests/ralph_log_sample.txt in project)",
)
def capture_fixture(log_file, output):
    "Extract representative lines from a ralph log to build a test fixture"
    project = Path(config.project)
    log_path = Path(log_file) if log_file else project / ".ralph-log"
    output_path = Path(output) if output else project / "tests" / "ralph_log_sample.txt"

    if not log_path.exists():
        raise click.ClickException(f"log file not found: {log_path}")

    lines = log_path.read_text().splitlines(keepends=True)

    # Patterns for each filter branch, in priority order.
    # We collect the first (shortest) match for each.
    patterns = [
        ("ralph-wrapper-start", r"\[ralph-wrapper\] start"),
        ("ralph-wrapper-other", r"\[ralph-wrapper\] ralph (?:started|exited)"),
        ("ralph-wrapper-level", r"\[ralph-wrapper\] log-level:"),
        ("tool-read", r'"name":"Read"'),
        ("tool-bash", r'"name":"Bash"'),
        ("tool-grep", r'"name":"Grep"'),
        ("tool-edit", r'"name":"Edit"'),
        ("tool-write", r'"name":"Write"'),
        ("event", r"Event emitted"),
        ("git-commit", r"git commit -m"),
        ("test-pass", r"\d+ passed"),
        ("test-fail", r"FAILED.*test_use_case"),
    ]

    max_len = 2000  # skip giant JSON blobs

    selected = {}
    for label, pattern in patterns:
        if label in selected:
            continue
        best = None
        for line in lines:
            if len(line) > max_len:
                continue
            if re.search(pattern, line):
                if best is None or len(line) < len(best):
                    best = line
        if best is not None:
            selected[label] = best

    # Always include one unmatched line (for verbose catch-all)
    for line in lines:
        if len(line) > max_len:
            continue
        matched = any(re.search(p, line) for _, p in patterns)
        if not matched and line.strip():
            selected["unmatched"] = line
            break

    if not selected:
        raise click.ClickException("no matching lines found in log")

    # Write in a stable order. log-level goes last since it changes
    # filter mode and would affect processing of subsequent lines.
    order = [p[0] for p in patterns if p[0] != "ralph-wrapper-level"] + [
        "unmatched",
        "ralph-wrapper-level",
    ]
    fixture_lines = [selected[k] for k in order if k in selected]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for line in fixture_lines:
            f.write(line if line.endswith("\n") else line + "\n")

    print(f"Wrote {len(fixture_lines)} lines to {output_path}")
    for label in order:
        if label in selected:
            print(f"  {label}: {len(selected[label].strip())} chars")


# clk commands:1 ends here
