# [[file:../dev.org::+begin_src python][No heading:1]]
from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function, object_type

DAGGER_VERSION = "0.20.3"
ORG_PIN = "1025e3b49a98f175b124dbccd774918360fe7e11"
# No heading:1 ends here


# [[file:../dev.org::*Dev class][Dev class:1]]
@object_type
class Dev:
    @function
    def container(self) -> dagger.Container:
        """Dev container with emacs, git, ruff, pytest, and dagger CLI."""
        ctr = (
            dag.container()
            .from_("debian:bookworm-slim")
            .with_exec(
                [
                    "apt-get",
                    "update",
                ]
            )
            .with_exec(
                [
                    "apt-get",
                    "install",
                    "-y",
                    "--no-install-recommends",
                    "emacs-nox",
                    "git",
                    "python3",
                    "python3-pip",
                    "python3-venv",
                    "curl",
                    "ca-certificates",
                ]
            )
            .with_exec(
                [
                    "pip",
                    "install",
                    "--break-system-packages",
                    "ruff",
                    "pytest",
                ]
            )
            .with_exec(
                [
                    "sh",
                    "-c",
                    f"curl -fsSL https://dl.dagger.io/dagger/install.sh"
                    f" | DAGGER_VERSION={DAGGER_VERSION} BIN_DIR=/usr/local/bin sh",
                ]
            )
        )
        # Clone and set up pinned org-mode (cached in this layer)
        ctr = (
            ctr.with_exec(
                [
                    "git",
                    "clone",
                    "--quiet",
                    "https://git.savannah.gnu.org/git/emacs/org-mode.git",
                    "/opt/org",
                ]
            )
            .with_exec(["git", "-C", "/opt/org", "checkout", "--quiet", ORG_PIN])
            .with_exec(
                [
                    "emacs",
                    "--batch",
                    "--no-init-file",
                    "--eval",
                    "(progn"
                    '  (push "/opt/org/lisp" load-path)'
                    "  (require (quote autoload))"
                    '  (setq generated-autoload-file "/opt/org/lisp/org-loaddefs.el")'
                    '  (update-directory-autoloads "/opt/org/lisp"))',
                ]
            )
            .with_exec(
                [
                    "sh",
                    "-c",
                    "cd /opt/org/lisp && emacs --batch --no-init-file"
                    " --eval '(progn"
                    '  (push \\"/opt/org/lisp\\" load-path)'
                    '  (load \\"/opt/org/mk/org-fixup.el\\")'
                    "  (org-make-org-version"
                    '    \\"0\\" \\"0\\"))\' 2>/dev/null || true',
                ]
            )
        )
        return ctr

    @function
    async def tangle(
        self,
        source: Annotated[dagger.Directory, DefaultPath(".")],
    ) -> dagger.Directory:
        """Tangle all org files, returning the directory with generated code."""
        return await (
            self.container()
            .with_workdir("/work")
            .with_directory("/work", source)
            .with_exec(
                [
                    "sh",
                    "-c",
                    "mkdir -p .tangle-deps && ln -sf /opt/org .tangle-deps/org",
                ]
            )
            .with_exec(
                [
                    "sh",
                    "-c",
                    "./tangle-nodagger.sh"
                    " readme.org TECHNICAL.org src/*.org tests/*.org doc/*.org",
                ]
            )
            .directory("/work")
        )

    @function
    async def run(
        self,
        source: Annotated[dagger.Directory, DefaultPath(".")],
    ) -> dagger.Directory:
        """Execute org-babel blocks and save results."""
        return await (
            self.container()
            .with_workdir("/work")
            .with_directory("/work", source)
            .with_exec(
                [
                    "sh",
                    "-c",
                    "mkdir -p .tangle-deps && ln -sf /opt/org .tangle-deps/org",
                ]
            )
            .with_exec(
                ["./run-nodagger.sh"],
                experimental_privileged_nesting=True,
            )
            .directory("/work")
        )

    @function
    async def test(
        self,
        source: Annotated[dagger.Directory, DefaultPath(".")],
    ) -> str:
        """Run the test suite."""
        return await (
            self.container()
            .with_workdir("/work")
            .with_directory("/work", source)
            .with_exec(
                ["./test-nodagger.sh"],
                experimental_privileged_nesting=True,
            )
            .stdout()
        )


# Dev class:1 ends here
