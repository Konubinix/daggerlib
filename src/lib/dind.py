# [[file:../dind.org::+begin_src python :tangle lib/dind.py :noweb yes][No heading:1]]
import dagger
from dagger import dag, function


_DIND_DNS_ENTRYPOINT = """\
#!/bin/sh
DNS_SERVER=$(awk '/^nameserver/{print $2; exit}' /etc/resolv.conf)
iptables -t nat -A PREROUTING -p udp -d 172.17.0.1 --dport 53 \
    -j DNAT --to-destination "$DNS_SERVER:53" 2>/dev/null || true
iptables -t nat -A PREROUTING -p tcp -d 172.17.0.1 --dport 53 \
    -j DNAT --to-destination "$DNS_SERVER:53" 2>/dev/null || true
exec dockerd-entrypoint-orig.sh "$@"
"""


class DindMixin:
    @function
    def dind_service(self) -> dagger.Service:
        """Return a Docker daemon running as a sidecar service.

        Wraps the docker:dind entrypoint with DNS forwarding so
        nested Dagger engines can resolve names despite the
        10.87.0.0/16 subnet collision.
        """
        return (
            dag.container()
            .from_(self.pinned(self._dind_engine_image))
            .with_env_variable("DOCKER_TLS_CERTDIR", "")
            .with_env_variable("TINI_SUBREAPER", "")
            .with_new_file(
                "/etc/docker/daemon.json",
                '{"dns": ["172.17.0.1"]}',
            )
            .with_exec(
                [
                    "mv",
                    "/usr/local/bin/dockerd-entrypoint.sh",
                    "/usr/local/bin/dockerd-entrypoint-orig.sh",
                ]
            )
            .with_new_file(
                "/usr/local/bin/dockerd-entrypoint.sh",
                _DIND_DNS_ENTRYPOINT,
                permissions=0o755,
            )
            .with_mounted_cache("/var/lib/docker", dag.cache_volume("dind-docker"))
            .with_exposed_port(2375)
            .as_service(
                use_entrypoint=True,
                insecure_root_capabilities=True,
            )
        )

    @function
    def dind_container(
        self,
        base: dagger.Container | None = None,
    ) -> dagger.Container:
        """Return a container with the Docker CLI installed.

        If base is provided, the CLI is added to it.
        Otherwise uses Lib.dind_ubuntu_image.
        """
        if base is None:
            base = dag.container().from_(self.pinned(self._dind_base_image))
        docker_cli = (
            dag.container()
            .from_(self.pinned(self._dind_engine_image))
            .file("/usr/local/bin/docker")
        )
        return base.with_file("/usr/local/bin/docker", docker_cli)

    @function
    def dind_with_docker(
        self,
        cmd: str,
        ctr: dagger.Container | None = None,
    ) -> dagger.Container:
        """Run a shell command inside a container with Docker available.

        Binds a Docker daemon sidecar and sets DOCKER_HOST so the
        Docker CLI in the container talks to the sidecar over TCP.
        """
        if ctr is None:
            ctr = self.dind_container()
        return (
            ctr.with_service_binding("docker", self.dind_service())
            .with_env_variable("DOCKER_HOST", "tcp://docker:2375")
            .with_exec(["bash", "-c", cmd])
        )

    @function
    def dind_run_tests(self) -> dagger.Container:
        """Run the project test suite inside Docker-in-Docker (dogfooding).

        Builds a test-ready container from the DinD base, installs Python,
        pytest, and the Dagger CLI, mounts the project source, and runs
        ./test-host.sh with dockerd available.
        Source is mounted last so package installs are cached.
        """
        src = dag.directory().with_directory(
            ".",
            dag.current_module().source(),
            include=[
                "src/lib/",
                "src/ralph.yml",
                "sdk/",
                "tests/",
                "examples/",
                "dagger.json",
                ".daggerignore",
                "pyproject.toml",
                "test-host.sh",
            ],
        )

        ctr = self.dind_container()
        ctr = (
            ctr.with_exec(["apt-get", "update"])
            .with_exec(
                [
                    "apt-get",
                    "install",
                    "--yes",
                    "curl",
                    "python3",
                    "python3-pip",
                    "python3-venv",
                ]
            )
            .with_exec(
                [
                    "pip3",
                    "install",
                    "--break-system-packages",
                    "pytest",
                    "pytest-asyncio",
                ]
            )
            .with_exec(
                [
                    "bash",
                    "-c",
                    "curl -fsSL https://dl.dagger.io/dagger/install.sh"
                    " | DAGGER_VERSION=0.20.3 BIN_DIR=/usr/local/bin sh",
                ]
            )
            .with_directory("/work", src)
            .with_workdir("/work")
            .with_directory("/work/.git", dag.directory())
        )
        cmd = (
            "echo '=== dockerd ready ===' && "
            "docker info --format 'Docker: {{.ServerVersion}}' && "
            "echo '=== running test suite ===' && "
            "./test-host.sh"
        )
        return self.dind_with_docker(cmd=cmd, ctr=ctr)

    @function
    def emacs_container(
        self,
        src: dagger.Directory,
    ) -> dagger.Container:
        """Return a lightweight container with emacs, git, python, and ruff."""
        return (
            dag.container()
            .from_(self.pinned(self._dind_base_image))
            .with_exec(["apt-get", "update"])
            .with_exec(
                [
                    "apt-get",
                    "install",
                    "--yes",
                    "emacs-nox",
                    "git",
                    "python3",
                    "python3-pip",
                    "python3-venv",
                ]
            )
            .with_exec(
                [
                    "pip3",
                    "install",
                    "--break-system-packages",
                    "ruff",
                ]
            )
            .with_directory("/work", src)
            .with_workdir("/work")
        )

    @function
    def dind_emacs_container(self) -> dagger.Container:
        """Return a DinD container with emacs, git, python, ruff, and dagger CLI.

        Does NOT mount source — callers add it last so the entire
        tool install chain is cacheable.
        """
        ctr = self.dind_container()
        return (
            ctr.with_exec(["apt-get", "update"])
            .with_exec(
                [
                    "apt-get",
                    "install",
                    "--yes",
                    "curl",
                    "emacs-nox",
                    "git",
                    "python3",
                    "python3-pip",
                    "python3-venv",
                ]
            )
            .with_exec(
                [
                    "pip3",
                    "install",
                    "--break-system-packages",
                    "ruff",
                ]
            )
            .with_exec(
                [
                    "bash",
                    "-c",
                    "curl -fsSL https://dl.dagger.io/dagger/install.sh"
                    " | DAGGER_VERSION=0.20.3 BIN_DIR=/usr/local/bin sh",
                ]
            )
        )

    @function
    def dind_tangle(self) -> dagger.Directory:
        """Tangle org files inside a container and return only the modified files."""
        src = dag.directory().with_directory(
            ".",
            dag.current_module().source(),
            include=[
                "src/",
                "tests/",
                "examples/",
                ".clk/",
                "*.org",
                "*.sh",
                "*.el",
                "dagger.json",
            ],
        )
        ctr = self.emacs_container(src=src)
        ctr = ctr.with_mounted_cache(
            "/work/.tangle-deps", dag.cache_volume("tangle-deps")
        )
        before = ctr.directory("/work")
        after = ctr.with_exec(["./tangle-host.sh"]).directory("/work")
        return before.diff(after)

    @function
    def dind_run_org(
        self,
        files: list[str] | None = None,
        no_cache: bool = False,
    ) -> dagger.Directory:
        """Run org-babel blocks inside a DinD container and return only the modified files.

        If files is given, only those org files are processed.
        """
        src = dag.directory().with_directory(
            ".",
            dag.current_module().source(),
            include=[
                "src/",
                "examples/",
                "tests/dagger",
                "tests/ralph-log-filter",
                "tests/ralph_log_sample.txt",
                "*.org",
                "*.sh",
                "*.el",
                "dagger.json",
                ".daggerignore",
                "pyproject.toml",
                "sdk/",
            ],
        )
        ctr = self.dind_emacs_container()
        ctr = (
            ctr.with_directory("/work", src)
            .with_workdir("/work")
            .with_mounted_cache("/work/.tangle-deps", dag.cache_volume("tangle-deps"))
        )
        before = ctr.directory("/work")
        cmd = "./run-host.sh"
        if no_cache:
            cmd += " --no-cache"
        if files:
            cmd += " " + " ".join(files)
        after = self.dind_with_docker(cmd=cmd, ctr=ctr).directory("/work")
        return before.diff(after)

    @function
    def dind_init_examples(
        self,
        from_scratch: bool = False,
        no_cache: bool = False,
    ) -> dagger.Directory:
        """Init example modules inside a DinD container and return only the modified files."""
        src = dag.directory().with_directory(
            ".",
            dag.current_module().source(),
            include=[
                "src/lib/",
                "examples/",
                "*.sh",
                "*.el",
                "dagger.json",
                ".daggerignore",
                "pyproject.toml",
                "sdk/",
            ],
        )
        ctr = self.dind_emacs_container()
        ctr = (
            ctr.with_directory("/work", src)
            .with_workdir("/work")
            .with_mounted_cache("/work/.tangle-deps", dag.cache_volume("tangle-deps"))
        )
        before = ctr.directory("/work")
        cmd = "./init-examples-host.sh"
        if from_scratch:
            cmd += " --from-scratch"
        elif no_cache:
            cmd += " --no-cache"
        after = self.dind_with_docker(cmd=cmd, ctr=ctr).directory("/work")
        return before.diff(after)

    @function
    def export_html(self) -> dagger.Directory:
        """Export org files to HTML with noweb expansion for GitHub Pages."""
        src = dag.directory().with_directory(
            ".",
            dag.current_module().source(),
            include=[
                "src/*.org",
                "tests/testing.org",
                "examples/*/readme.org",
                "*.org",
                "*.sh",
                "*.el",
            ],
        )
        ctr = self.emacs_container(src=src)
        ctr = ctr.with_mounted_cache(
            "/work/.tangle-deps", dag.cache_volume("tangle-deps")
        )
        return ctr.with_exec(["./export-html-host.sh"]).directory("/work/_site")

    @property
    def _dind_engine_image(self) -> str:
        return self.dind_image

    @property
    def _dind_base_image(self) -> str:
        return self.dind_ubuntu_image


# No heading:1 ends here
