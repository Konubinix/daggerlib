# [[file:../dind.org::+begin_src python :tangle lib/dind.py :noweb yes][No heading:1]]
import dagger
from dagger import dag, function


_CGROUP_SETUP = (
    "mount -t cgroup2 cgroup2 /sys/fs/cgroup 2>/dev/null || true\n"
    "mkdir -p /sys/fs/cgroup/init\n"
    "xargs -rn1 < /sys/fs/cgroup/cgroup.procs > /sys/fs/cgroup/init/cgroup.procs 2>/dev/null || true\n"
    "sed -e 's/ / +/g' -e 's/^/+/' < /sys/fs/cgroup/cgroup.controllers"
    " > /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null || true\n"
)

_DNS_SETUP = (
    "DNS_SERVER=$(awk '/^nameserver/{print $2; exit}' /etc/resolv.conf)\n"
    "mkdir -p /etc/docker\n"
    'echo \'{"dns": ["172.17.0.1"]}\' > /etc/docker/daemon.json\n'
)

_DOCKERD_START = (
    "start_dockerd() {\n"
    "  rm -f /var/log/dockerd.log\n"
    "  mkdir -p /var/lib/docker\n"
    "  dockerd &>/var/log/dockerd.log &\n"
    "  for i in $(seq 1 30); do docker info &>/dev/null && return 0; sleep 0.2; done\n"
    "  kill %% 2>/dev/null; wait 2>/dev/null\n"
    "  return 1\n"
    "}\n"
    "if ! start_dockerd; then\n"
    "  echo 'dockerd failed to start, wiping /var/lib/docker and retrying...' >&2\n"
    "  rm -rf /var/lib/docker/*\n"
    "  if ! start_dockerd; then\n"
    "    echo '=== dockerd failed after wipe ===' >&2\n"
    "    cat /var/log/dockerd.log >&2\n"
    "    exit 1\n"
    "  fi\n"
    "fi\n"
    "iptables -t nat -A PREROUTING -p udp -d 172.17.0.1 --dport 53"
    " -j DNAT --to-destination $DNS_SERVER:53\n"
    "iptables -t nat -A PREROUTING -p tcp -d 172.17.0.1 --dport 53"
    " -j DNAT --to-destination $DNS_SERVER:53\n"
)


class DindMixin:
    _EMACS_INCLUDE = [
        "src/",
        "tests/",
        "examples/",
        ".clk/",
        "dagger.json",
        ".daggerignore",
        "pyproject.toml",
        "*.sh",
        "*.el",
        "*.org",
    ]

    @function
    def dind_container(
        self,
        base: dagger.Container | None = None,
    ) -> dagger.Container:
        """Return a container with Docker installed, ready for DinD.

        If base is provided, Docker is installed into it (must be
        Debian/Ubuntu-based).  Otherwise uses Lib.dind_ubuntu_image.
        The Docker APT repo setup is done inline so the container build
        has no dependency on the project source — only the base image and
        package versions affect the cache.
        """
        if base is None:
            base = dag.container().from_(self.dind_ubuntu_image)

        return (
            base.with_exec(["apt-get", "update"])
            .with_exec(
                [
                    "apt-get",
                    "install",
                    "--yes",
                    "ca-certificates",
                    "curl",
                    "gnupg",
                    "iptables",
                ]
            )
            .with_exec(
                [
                    "bash",
                    "-c",
                    ". /etc/os-release && "
                    "install -m 0755 -d /etc/apt/keyrings && "
                    "curl -fsSL https://download.docker.com/linux/$ID/gpg"
                    " -o /etc/apt/keyrings/docker.asc && "
                    "chmod a+r /etc/apt/keyrings/docker.asc && "
                    'echo "deb [arch=$(dpkg --print-architecture)'
                    " signed-by=/etc/apt/keyrings/docker.asc]"
                    " https://download.docker.com/linux/$ID"
                    ' $VERSION_CODENAME stable"'
                    " > /etc/apt/sources.list.d/docker.list && "
                    "apt-get update && "
                    "apt-get install --yes docker-ce docker-ce-cli containerd.io",
                ]
            )
        )

    @function
    def dind_with_docker(
        self,
        cmd: str,
        ctr: dagger.Container | None = None,
    ) -> dagger.Container:
        """Run a shell command inside the container with dockerd available.

        Handles cgroup v2 setup, tmpfs for /var/lib/docker,
        and dockerd lifecycle.  These must run in the same exec as the
        user command because processes and mounts do not persist across
        exec boundaries.
        """
        if ctr is None:
            ctr = self.dind_container()
        shell_cmd = _DNS_SETUP + _CGROUP_SETUP + _DOCKERD_START + cmd
        return ctr.with_exec(
            ["bash", "-c", shell_cmd],
            insecure_root_capabilities=True,
        )

    @function
    def dind_run_tests(self) -> dagger.Container:
        """Run the project test suite inside Docker-in-Docker (dogfooding).

        Builds a test-ready container from the DinD base, installs Python,
        pytest, and the Dagger CLI, mounts the project source, and runs
        ./test-host.sh with dockerd available.
        Source is mounted last so package installs are cached.
        """
        src = (
            dag.directory()
            .with_directory(
                ".",
                dag.current_module().source(),
                include=[
                    "src/",
                    "sdk/",
                    "tests/",
                    "examples/",
                    "dagger.json",
                    ".daggerignore",
                    "pyproject.toml",
                    "test-host.sh",
                ],
            )
            .with_new_directory(".git")
        )

        ctr = self.dind_container()
        ctr = (
            ctr.with_exec(
                [
                    "apt-get",
                    "install",
                    "--yes",
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
            .with_mounted_cache("/var/lib/docker", dag.cache_volume("dind-docker"))
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
            .from_(self.dind_ubuntu_image)
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
            ctr.with_exec(
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
            include=self._EMACS_INCLUDE,
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
            include=self._EMACS_INCLUDE,
        )
        ctr = self.dind_emacs_container()
        ctr = (
            ctr.with_directory("/work", src)
            .with_workdir("/work")
            .with_mounted_cache("/work/.tangle-deps", dag.cache_volume("tangle-deps"))
            .with_mounted_cache("/var/lib/docker", dag.cache_volume("dind-docker"))
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
            include=self._EMACS_INCLUDE,
        )
        ctr = self.dind_emacs_container()
        ctr = (
            ctr.with_directory("/work", src)
            .with_workdir("/work")
            .with_mounted_cache("/work/.tangle-deps", dag.cache_volume("tangle-deps"))
            .with_mounted_cache("/var/lib/docker", dag.cache_volume("dind-docker"))
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
            include=self._EMACS_INCLUDE,
        )
        ctr = self.emacs_container(src=src)
        ctr = ctr.with_mounted_cache(
            "/work/.tangle-deps", dag.cache_volume("tangle-deps")
        )
        return ctr.with_exec(["./export-html-host.sh"]).directory("/work/_site")


# No heading:1 ends here
