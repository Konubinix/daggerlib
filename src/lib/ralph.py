# [[file:../ralph.org::+begin_src python][No heading:1]]
import shlex
from pathlib import Path
from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function

_RALPH_WRAPPER_SH = (Path(__file__).parent / "ralph-wrapper.sh").read_text()
# No heading:1 ends here


# [[file:../ralph.org::*Running ralph in a container][Running ralph in a container:2]]
def _ralph_tooling(
    self,
    ctr: dagger.Container,
    home: str,
    dagger_runner_host: str,
) -> dagger.Container:
    """Install ralph CLI, claude-code, pytest, and dagger CLI."""
    q_home = shlex.quote(home)
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
    return ctr


def _ralph_git(
    self,
    ctr: dagger.Container,
    email: str,
    name: str,
) -> dagger.Container:
    """Configure git identity."""
    q_email = shlex.quote(email)
    q_name = shlex.quote(name)
    return ctr.with_exec(
        [
            "sh",
            "-c",
            f"git config --global user.email {q_email}"
            f" && git config --global user.name {q_name}"
            " && git config --global init.defaultBranch main",
        ]
    )


def _ralph_workdir(
    self,
    ctr: dagger.Container,
    src: dagger.Directory,
    work_dir: str,
    owner: str,
    ralph_yml: dagger.File | None,
    plan_md: dagger.File | None,
    todo_org: dagger.File | None,
) -> dagger.Container:
    """Copy project source and optional config files into workdir."""
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
    if ralph_yml is not None:
        ctr = ctr.with_file(f"{work_dir}/ralph.yml", ralph_yml, owner=owner)
    if plan_md is not None:
        ctr = ctr.with_file(f"{work_dir}/plan.md", plan_md, owner=owner)
    if todo_org is not None:
        ctr = ctr.with_file(f"{work_dir}/todo.org", todo_org, owner=owner)
    return ctr


def _ralph_credentials(
    self,
    ctr: dagger.Container,
    home: str,
    credentials: dagger.Secret,
    owner: str,
) -> dagger.Container:
    """Mount Claude credentials."""
    return ctr.with_exec(["mkdir", "-p", f"{home}/.claude"]).with_mounted_secret(
        f"{home}/.claude/.credentials.json",
        credentials,
        owner=owner,
    )


def _ralph_run(
    self,
    ctr: dagger.Container,
    work_dir: str,
    ralph_args: str,
    consul_addr: str,
    consul_key: str,
) -> dagger.Container:
    """Run ralph wrapper and generate patches."""
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
    q_work_dir = shlex.quote(work_dir)
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
    return ctr


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
    username: str | None = None,
    dagger_runner_host: str = "",
    consul_addr: str = "",
    consul_key: str = "ralph/dagger/status",
    ralph_yml: dagger.File | None = None,
    plan_md: dagger.File | None = None,
    todo_org: dagger.File | None = None,
) -> dagger.Directory:
    """Run ralph orchestrator in a container and return the workdir with patches."""
    username = username or self.default_username
    if ctr is None:
        ctr = self.debian_python_user_venv(
            extra_packages=["git", "npm"] + list(extra_packages),
        )
    owner = f"{username}:{username}"
    home = f"/home/{username}"
    ctr = self._ralph_tooling(ctr, home, dagger_runner_host)
    ctr = self._ralph_git(ctr, git_email, git_name)
    ctr = self._ralph_workdir(ctr, src, work_dir, owner, ralph_yml, plan_md, todo_org)
    ctr = self._ralph_credentials(ctr, home, claude_credentials, owner)
    ctr = self._ralph_run(ctr, work_dir, ralph_args, consul_addr, consul_key)
    return ctr.directory(work_dir)


# Running ralph in a container:2 ends here
