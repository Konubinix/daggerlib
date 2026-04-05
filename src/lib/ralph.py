# [[file:../ralph.org::+begin_src python][No heading:2]]
import shlex
from pathlib import Path
from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function

_RALPH_WRAPPER_SH = (Path(__file__).parent / "ralph-wrapper.sh").read_text()
# No heading:2 ends here


# [[file:../ralph.org::*Running ralph in a container][Running ralph in a container:2]]
@function
async def ralph(
    self,
    claude_credentials: dagger.Secret,
    src: Annotated[dagger.Directory, DefaultPath(".")],
    ctr: dagger.Container | None = None,
    extra_packages: list[str] = (),
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
            extra_packages=["git", "npm"] + list(extra_packages),
        )
    owner = f"{username}:{username}"
    home = f"/home/{username}"
    q_home = shlex.quote(home)
    # Install ralph-orchestrator and claude-code via npm
    ctr = ctr.with_exec(
        [
            "sh",
            "-c",
            f"npm config set prefix {q_home}/.npm-global"
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
            f"cd {q_home} && curl -fsSL https://dl.dagger.io/dagger/install.sh"
            " | BIN_DIR=$HOME/.local/bin sh",
        ]
    )
    if dagger_runner_host:
        ctr = ctr.with_env_variable(
            "_EXPERIMENTAL_DAGGER_RUNNER_HOST",
            dagger_runner_host,
        )
    # Configure git identity
    q_email = shlex.quote(git_email)
    q_name = shlex.quote(git_name)
    ctr = ctr.with_exec(
        [
            "sh",
            "-c",
            f"git config --global user.email {q_email}"
            f" && git config --global user.name {q_name}"
            " && git config --global init.defaultBranch main",
        ]
    )
    # Copy project source (including .git) into workdir
    q_work_dir = shlex.quote(work_dir)
    ctr = (
        ctr.with_directory(
            f"{work_dir}/.git",
            src.directory(".git"),
            owner=owner,
        )
        .with_directory(work_dir, src, owner=owner)
        .with_exec(["sh", "-c", f"cd {q_work_dir} && git checkout ."])
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
    # Mount and run the ralph wrapper script
    ctr = (
        ctr.with_new_file(
            "/tmp/ralph-wrapper.sh",
            _RALPH_WRAPPER_SH,
        )
        .with_env_variable(
            "WORK_DIR",
            work_dir,
        )
        .with_env_variable(
            "RALPH_ARGS",
            ralph_args,
        )
    )
    if consul_addr:
        ctr = ctr.with_env_variable(
            "CONSUL_ADDR",
            consul_addr,
        ).with_env_variable(
            "CONSUL_KEY",
            consul_key,
        )
    ctr = ctr.with_exec(["sh", "/tmp/ralph-wrapper.sh"])
    # Generate format-patch files for all new commits
    ctr = ctr.with_exec(
        [
            "sh",
            "-c",
            f"cd {q_work_dir}"
            " && mkdir -p patches"
            " && base=$(cat /tmp/ralph-base-commit)"
            ' && if [ "$(git rev-parse HEAD)" != "$base" ]; then'
            ' git format-patch "$base"..HEAD -o patches;'
            " fi",
        ]
    )
    return ctr.directory(work_dir)


# Running ralph in a container:2 ends here
