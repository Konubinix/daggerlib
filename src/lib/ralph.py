# [[file:../ralph.org::+begin_src python][No heading:2]]
from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function
# No heading:2 ends here


# [[file:../ralph.org::*Running ralph in a container][Running ralph in a container:1]]
@function
async def ralph(
    self,
    claude_credentials: dagger.Secret,
    src: Annotated[dagger.Directory, DefaultPath(".")],
    ctr: dagger.Container | None = None,
    extra_packages: str = "",
    ralph_args: str = "",
    work_dir: str = "/tmp/ralph-workdir",
    git_email: str = "ralph@localhost",
    git_name: str = "Ralph",
    username: str = "sam",
    dagger_runner_host: str = "",
    consul_addr: str = "",
    consul_key: str = "ralph/dagger/status",
    ralph_yml: dagger.File | None = None,
    plan_md: dagger.File | None = None,
    todo_org: dagger.File | None = None,
) -> dagger.Directory:
    """Run ralph orchestrator in a container and return the workdir with patches."""
    if ctr is None:
        ctr = self.debian_python_user_venv(
            extra_packages=f"git npm {extra_packages}".strip(),
        )
    owner = f"{username}:{username}"
    home = f"/home/{username}"
    # Install ralph-orchestrator and claude-code via npm
    ctr = ctr.with_exec(
        [
            "sh",
            "-c",
            f'npm config set prefix "{home}/.npm-global"'
            " && npm install -g"
            " @ralph-orchestrator/ralph-cli"
            " @anthropic-ai/claude-code",
        ]
    ).with_env_variable(
        "PATH",
        f"{home}/.npm-global/bin:$PATH",
        expand=True,
    )
    # Install pytest and dagger CLI for running tests inside the container
    ctr = ctr.with_exec(["sh", "-c", "pip install --quiet pytest"]).with_exec(
        [
            "sh",
            "-c",
            f"cd {home} && curl -fsSL https://dl.dagger.io/dagger/install.sh"
            " | BIN_DIR=$HOME/.local/bin sh",
        ]
    )
    if dagger_runner_host:
        ctr = ctr.with_env_variable(
            "_EXPERIMENTAL_DAGGER_RUNNER_HOST",
            dagger_runner_host,
        )
    # Configure git identity
    ctr = ctr.with_exec(
        [
            "sh",
            "-c",
            f'git config --global user.email "{git_email}"'
            f' && git config --global user.name "{git_name}"'
            " && git config --global init.defaultBranch main",
        ]
    )
    # Copy project source (including .git) into workdir
    ctr = (
        ctr.with_directory(
            f"{work_dir}/.git",
            src.directory(".git"),
            owner=owner,
        )
        .with_directory(work_dir, src, owner=owner)
        .with_exec(["sh", "-c", f"cd {work_dir} && git checkout ."])
    )
    # Optional config files
    if ralph_yml is not None:
        ctr = ctr.with_file(f"{work_dir}/ralph.yml", ralph_yml, owner=owner)
    if plan_md is not None:
        ctr = ctr.with_file(f"{work_dir}/plan.md", plan_md, owner=owner)
    if todo_org is not None:
        ctr = ctr.with_file(f"{work_dir}/todo.org", todo_org, owner=owner)
    # Mount credentials and run ralph
    ctr = ctr.with_exec(["mkdir", "-p", f"{home}/.claude"]).with_mounted_secret(
        f"{home}/.claude/.credentials.json",
        claude_credentials,
        owner=owner,
    )
    # Build the run command: ralph in background + optional Consul polling
    run_cmd = (
        f"cd {work_dir}"
        " && git rev-parse HEAD > /tmp/ralph-base-commit"
        ' && echo "[ralph-wrapper] starting ralph..."'
        f' && eval "ralph {ralph_args}" &'
        " RALPH_PID=$!;"
        ' echo "[ralph-wrapper] ralph started (PID $RALPH_PID)";'
    )
    if consul_addr:
        run_cmd += (
            ' echo "[ralph-wrapper] polling consul at {consul_addr} key={consul_key}";'
            " while kill -0 $RALPH_PID 2>/dev/null; do"
            f'   status=$(curl -sf "{consul_addr}/v1/kv/{consul_key}?raw" 2>/dev/null || echo running);'
            '   if [ "$status" = "stop" ]; then'
            '     echo "[ralph-wrapper] stop signal received, sending SIGTERM to ralph (PID $RALPH_PID)...";'
            "     kill -TERM $RALPH_PID 2>/dev/null || true;"
            "     for i in $(seq 1 30); do"
            "       kill -0 $RALPH_PID 2>/dev/null || break;"
            "       sleep 1;"
            "     done;"
            "     if kill -0 $RALPH_PID 2>/dev/null; then"
            '       echo "[ralph-wrapper] ralph did not exit after 30s, sending SIGKILL";'
            "       kill -KILL $RALPH_PID 2>/dev/null || true;"
            "     fi;"
            "     break;"
            "   fi;"
            "   sleep 5;"
            " done;"
        )
    run_cmd += (
        ' echo "[ralph-wrapper] waiting for ralph to exit...";'
        " wait $RALPH_PID;"
        " RC=$?;"
        ' echo "[ralph-wrapper] ralph exited with code $RC";'
        f" echo ${{RC}} > {work_dir}/.ralph-exit-code;"
        " true"
    )
    ctr = ctr.with_exec(["sh", "-c", run_cmd])
    # Generate format-patch files for all new commits
    ctr = ctr.with_exec(
        [
            "sh",
            "-c",
            f"cd {work_dir}"
            " && mkdir -p patches"
            " && base=$(cat /tmp/ralph-base-commit)"
            ' && if [ "$(git rev-parse HEAD)" != "$base" ]; then'
            ' git format-patch "$base"..HEAD -o patches;'
            " fi",
        ]
    )
    return ctr.directory(work_dir)


# Running ralph in a container:1 ends here
