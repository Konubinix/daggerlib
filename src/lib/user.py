# [[file:../user.org::+begin_src python][No heading:2]]
import shlex

import dagger
from dagger import function
# No heading:2 ends here


# [[file:../user.org::*Creating a user with groups and sudo][Creating a user with groups and sudo:1]]
@function
def setup_user(
    self,
    ctr: dagger.Container,
    uid: int = 1000,
    username: str = "sam",
    sudoer: bool = False,
    shell: str = "/bin/sh",
    groups: list[str] = (),
) -> dagger.Container:
    """Create a user with optional groups and sudo access."""
    q_username = shlex.quote(username)
    q_shell = shlex.quote(shell)
    ctr = (
        ctr.with_env_variable("HOME", f"/home/{username}")
        .with_exec(
            [
                "sh",
                "-c",
                "if ! which addgroup && which apt ; then"
                " apt update && apt install --yes adduser ; fi",
            ]
        )
        .with_exec(
            [
                "sh",
                "-c",
                f"addgroup --gid {uid} --system {q_username}"
                f" && adduser --uid {uid} --shell {q_shell}"
                f" --disabled-password --gecos '' {q_username}"
                f" --ingroup {q_username}"
                f" && chown -R {q_username}:{q_username} /home/{q_username}",
            ]
        )
    )
    if sudoer:
        ctr = ctr.with_exec(
            [
                "sh",
                "-c",
                f"mkdir -p /etc/sudoers.d"
                f' && echo "{q_username} ALL=(ALL) NOPASSWD: ALL"'
                f" >> /etc/sudoers.d/username",
            ]
        )
    if groups:
        groups_str = " ".join(shlex.quote(g) for g in groups)
        ctr = ctr.with_exec(
            [
                "sh",
                "-c",
                f"for group in {groups_str} ; do"
                f' {{ grep -q -E "^${{group}}:" /etc/group'
                f" || addgroup --system $group ; }}"
                f" && adduser {q_username} $group ; done",
            ]
        )
    ctr = ctr.with_env_variable(
        "PATH",
        f"/home/{username}/.local/bin:$PATH",
        expand=True,
    )
    return ctr


# Creating a user with groups and sudo:1 ends here


# [[file:../user.org::*Switching to a user][Switching to a user:1]]
@function
def as_user(
    self,
    ctr: dagger.Container,
    uid: int = 1000,
    username: str = "sam",
) -> dagger.Container:
    """Switch to user and set workdir to their home."""
    return (
        ctr.with_env_variable("HOME", f"/home/{username}")
        .with_user(username)
        .with_workdir(f"/home/{username}")
    )


# Switching to a user:1 ends here


# [[file:../user.org::*The full combo: create + switch][The full combo: create + switch:1]]
@function
def use_user(
    self,
    ctr: dagger.Container,
    groups: list[str] = (),
    uid: int = 1000,
    sudoer: bool = False,
    username: str = "sam",
) -> dagger.Container:
    """Create a user and switch to it (SETUP_USER + AS_USER)."""
    ctr = self.setup_user(ctr, uid=uid, username=username, sudoer=sudoer, groups=groups)
    ctr = self.as_user(ctr, uid=uid, username=username)
    return ctr


# The full combo: create + switch:1 ends here


# [[file:../user.org::*Writing environment variables to the user's profile][Writing environment variables to the user's profile:1]]
@function
def user_write_env(
    self,
    ctr: dagger.Container,
    name: str,
) -> dagger.Container:
    """Append an export line for a variable to ~/.profile."""
    q_name = shlex.quote(name)
    return ctr.with_exec(
        [
            "bash",
            "-c",
            f'echo export {q_name}="${{{q_name}}}"' + " >> ${HOME}/.profile",
        ]
    )


# Writing environment variables to the user's profile:1 ends here
