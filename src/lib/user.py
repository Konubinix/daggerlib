# [[file:../user.org::+begin_src python :tangle lib/user.py :noweb yes :exports none][No heading:1]]
import shlex

import dagger
from dagger import function


class UserMixin:

    @function
    def setup_user(
        self,
        ctr: dagger.Container,
        uid: int = 1000,
        username: str | None = None,
        sudoer: bool = False,
        shell: str = "/bin/sh",
        groups: list[str] = (),
    ) -> dagger.Container:
        """Create a user with optional groups and sudo access."""
        username = username or self.default_username
        q_username, q_shell = map(shlex.quote, (username, shell))
        ctr = (
            ctr
            .with_env_variable("HOME", f"/home/{username}")
            .with_exec([
                "sh", "-c",
                "command -v adduser > /dev/null"
                " || { command -v apt > /dev/null"
                " && apt update && apt install --yes adduser ; }",
            ])
            .with_exec([
                "sh", "-c",
                f"addgroup --gid {uid} --system {q_username}"
                f" && adduser --uid {uid} --shell {q_shell}"
                f" --disabled-password --gecos '' {q_username}"
                f" --ingroup {q_username}"
                f" && chown -R {q_username}:{q_username} /home/{q_username}",
            ])
        )
        if sudoer:
            ctr = ctr.with_exec([
                "sh", "-c",
                f'mkdir -p /etc/sudoers.d'
                f' && echo "{q_username} ALL=(ALL) NOPASSWD: ALL"'
                f' >> /etc/sudoers.d/username',
            ])
        if groups:
            groups_str = shlex.join(groups)
            ctr = ctr.with_exec([
                "sh", "-c",
                f"for group in {groups_str} ; do"
                f' {{ grep -q -E "^${{group}}:" /etc/group'
                f" || addgroup --system $group ; }}"
                f" && adduser {q_username} $group ; done",
            ])
        ctr = ctr.with_env_variable(
            "PATH", f"/home/{username}/.local/bin:$PATH", expand=True,
        )
        return ctr

    @function
    def as_user(
        self,
        ctr: dagger.Container,
        username: str | None = None,
    ) -> dagger.Container:
        """Switch to user and set workdir to their home."""
        username = username or self.default_username
        return (
            ctr
            .with_env_variable("HOME", f"/home/{username}")
            .with_user(username)
            .with_workdir(f"/home/{username}")
        )

    @function
    def use_user(
        self,
        ctr: dagger.Container,
        uid: int = 1000,
        username: str | None = None,
        sudoer: bool = False,
        groups: list[str] = (),
    ) -> dagger.Container:
        """Create a user and switch to it (SETUP_USER + AS_USER)."""
        ctr = self.setup_user(ctr, uid=uid, username=username, sudoer=sudoer, groups=groups)
        ctr = self.as_user(ctr, username=username)
        return ctr
# No heading:1 ends here
