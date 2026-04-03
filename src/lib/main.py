import dagger
from dagger import dag, function, object_type


_CGROUP_SETUP = (
    "mount -t cgroup2 cgroup2 /sys/fs/cgroup 2>/dev/null || true\n"
    "mkdir -p /sys/fs/cgroup/init\n"
    "xargs -rn1 < /sys/fs/cgroup/cgroup.procs > /sys/fs/cgroup/init/cgroup.procs 2>/dev/null || true\n"
    "sed -e 's/ / +/g' -e 's/^/+/' < /sys/fs/cgroup/cgroup.controllers"
    " > /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null || true\n"
)

_DOCKERD_START = (
    "mkdir -p /var/lib/docker\n"
    "mount -t tmpfs tmpfs /var/lib/docker\n"
    "dockerd &>/var/log/dockerd.log &\n"
    "sleep 3\n"
)


@object_type
class Lib:
    debian_version: str = "13"
    debian_min_version: str = "2"

    # ── Reusable functions (Earthly FUNCTIONs) ──────────────────────────

    @function
    def alpine_tz_fr(self, ctr: dagger.Container) -> dagger.Container:
        """Set timezone to Europe/Paris on an Alpine container."""
        return ctr.with_exec([
            "sh", "-c",
            "apk --quiet add --update tzdata"
            " && cp /usr/share/zoneinfo/Europe/Paris /etc/localtime"
            ' && echo "Europe/Paris" > /etc/timezone'
            " && apk --quiet del tzdata",
        ])

    @function
    def python_venv(
        self,
        ctr: dagger.Container,
        base: str,
        packages: str = "",
    ) -> dagger.Container:
        """Create a Python venv with --system-site-packages and optionally install packages."""
        ctr = ctr.with_exec([
            "python3", "-m", "venv", "--system-site-packages", f"{base}/venv",
        ]).with_env_variable("PATH", f"{base}/venv/bin:$PATH", expand=True)
        if packages:
            ctr = ctr.with_exec([
                "sh", "-c",
                f"{base}/venv/bin/python -m pip --quiet install --upgrade {packages}",
            ])
        return ctr

    @function
    def debian_apt_cleanup(self, ctr: dagger.Container) -> dagger.Container:
        """Clean apt caches."""
        return ctr.with_exec([
            "sh", "-c",
            "apt-get --quiet clean && rm -rf /var/lib/apt/lists/*",
        ])

    @function
    def debian_tz_fr(self, ctr: dagger.Container) -> dagger.Container:
        """Set timezone to Europe/Paris on a Debian container."""
        return (
            ctr
            .with_exec(["rm", "/etc/localtime"])
            .with_exec(["ln", "-sf", "/usr/share/zoneinfo/Europe/Paris", "/etc/localtime"])
        )

    @function
    def distroless_tz_fr(self, ctr: dagger.Container) -> dagger.Container:
        """Copy Europe/Paris localtime into a distroless container."""
        return ctr.with_file("/etc/localtime", self.debian_europe_paris())

    @function
    def setup_user(
        self,
        ctr: dagger.Container,
        uid: int = 1000,
        username: str = "sam",
        sudoer: bool = False,
        shell: str = "/bin/sh",
        groups: str = "",
    ) -> dagger.Container:
        """Create a user with optional groups and sudo access."""
        ctr = (
            ctr
            .with_env_variable("HOME", f"/home/{username}")
            .with_exec([
                "sh", "-c",
                "if ! which addgroup && which apt ; then"
                " apt update && apt install --yes adduser ; fi",
            ])
            .with_exec([
                "sh", "-c",
                f"addgroup --gid {uid} --system {username}"
                f" && adduser --uid {uid} --shell {shell}"
                f" --disabled-password --gecos '' {username}"
                f" --ingroup {username}"
                f" && chown -R {username}:{username} /home/{username}",
            ])
        )
        if sudoer:
            ctr = ctr.with_exec([
                "sh", "-c",
                f'mkdir -p /etc/sudoers.d'
                f' && echo "{username} ALL=(ALL) NOPASSWD: ALL"'
                f' >> /etc/sudoers.d/username',
            ])
        if groups:
            ctr = ctr.with_exec([
                "sh", "-c",
                f"for group in {groups} ; do"
                f' {{ grep -q -E "^${{group}}:" /etc/group'
                f" || addgroup --system $group ; }}"
                f" && adduser {username} $group ; done",
            ])
        ctr = ctr.with_env_variable(
            "PATH", f"/home/{username}/.local/bin:$PATH", expand=True,
        )
        return ctr

    @function
    def as_user(
        self,
        ctr: dagger.Container,
        uid: int = 1000,
        username: str = "sam",
    ) -> dagger.Container:
        """Switch to user and set workdir to their home."""
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
        groups: str = "",
        uid: int = 1000,
        sudoer: bool = False,
        username: str = "sam",
    ) -> dagger.Container:
        """Create a user and switch to it (SETUP_USER + AS_USER)."""
        ctr = self.setup_user(ctr, uid=uid, username=username, sudoer=sudoer, groups=groups)
        ctr = self.as_user(ctr, uid=uid, username=username)
        return ctr

    @function
    def debian_no_auto_install(self, ctr: dagger.Container) -> dagger.Container:
        """Disable apt recommends and suggests."""
        return ctr.with_exec([
            "sh", "-c",
            'echo \'APT::Install-Recommends "0";\' > /etc/apt/apt.conf.d/01norecommend'
            " && "
            'echo \'APT::Install-Suggests "0";\' >> /etc/apt/apt.conf.d/01norecommend',
        ])

    @function
    def user_write_env(
        self,
        ctr: dagger.Container,
        name: str,
    ) -> dagger.Container:
        """Append an export line for a variable to ~/.profile."""
        return ctr.with_exec([
            "bash", "-c",
            f'echo export {name}="${{{name}}}"' + " >> ${HOME}/.profile",
        ])

    # ── Base image targets (Earthly targets) ────────────────────────────

    @function
    def alpine(self, extra_packages: str = "") -> dagger.Container:
        """Alpine 3.23 with Europe/Paris timezone and optional extra packages."""
        ctr = dag.container().from_("alpine:3.23")
        ctr = self.alpine_tz_fr(ctr)
        if extra_packages:
            ctr = ctr.with_exec([
                "sh", "-c", f"apk --quiet add {extra_packages}",
            ])
        return ctr

    @function
    def alpine_user(
        self,
        extra_packages: str = "",
        groups: str = "",
    ) -> dagger.Container:
        """Alpine with a default user."""
        ctr = self.alpine(extra_packages=extra_packages)
        return self.use_user(ctr, groups=groups)

    @function
    def alpine_tz(self) -> dagger.Directory:
        """Extract /etc/localtime and /etc/timezone from Alpine as artifacts."""
        ctr = self.alpine()
        return (
            dag.directory()
            .with_file("localtime", ctr.file("/etc/localtime"))
            .with_file("timezone", ctr.file("/etc/timezone"))
        )

    @function
    def alpine_python(self, extra_packages: str = "") -> dagger.Container:
        """Alpine with python3 and pip."""
        return self.alpine(extra_packages=f"python3 py3-pip {extra_packages}".strip())

    @function
    def alpine_python_user_venv(
        self,
        extra_packages: str = "",
        groups: str = "",
        packages: str = "",
        workdir: str = "/app",
    ) -> dagger.Container:
        """Alpine with python, user, and a virtualenv."""
        ctr = self.alpine_python(extra_packages=extra_packages)
        ctr = self.use_user(ctr, groups=groups)
        ctr = ctr.with_workdir(workdir)
        return self.python_venv(ctr, base=workdir, packages=packages)

    @function
    def debian(self, extra_packages: str = "") -> dagger.Container:
        """Debian slim with Europe/Paris timezone, no auto-install, and optional extra packages."""
        tag = f"{self.debian_version}.{self.debian_min_version}-slim"
        ctr = dag.container().from_(f"debian:{tag}")
        ctr = self.debian_no_auto_install(ctr)
        ctr = self.debian_tz_fr(ctr)
        if extra_packages:
            ctr = ctr.with_exec([
                "sh", "-c",
                "{ apt-get --quiet update"
                f" && apt-get --quiet install --yes {extra_packages}"
                " ; } > /tmp/log 2>&1 || { cat /tmp/log; exit 1; }",
            ])
            ctr = self.debian_apt_cleanup(ctr)
        return ctr

    @function
    def debian_user(self, extra_packages: str = "") -> dagger.Container:
        """Debian with a default user."""
        ctr = self.debian(extra_packages=extra_packages)
        return self.use_user(ctr)

    @function
    def debian_python_user_venv(
        self,
        extra_packages: str = "",
        groups: str = "",
        packages: str = "",
        workdir: str = "/app",
    ) -> dagger.Container:
        """Debian with python, user, and a virtualenv."""
        ctr = self.debian(extra_packages=f"python3-venv {extra_packages}".strip())
        ctr = self.use_user(ctr, groups=groups)
        ctr = ctr.with_workdir(workdir)
        return self.python_venv(ctr, base=workdir, packages=packages)

    @function
    def debian_europe_paris(self) -> dagger.File:
        """Extract the Europe/Paris localtime file from Debian."""
        tag = f"{self.debian_version}.{self.debian_min_version}-slim"
        return (
            dag.container()
            .from_(f"debian:{tag}")
            .file("/usr/share/zoneinfo/Europe/Paris")
        )

    @function
    def distroless_python3_debian(self) -> dagger.Container:
        """Distroless python3 with Europe/Paris timezone."""
        ctr = dag.container().from_(
            f"gcr.io/distroless/python3-debian{self.debian_version}"
        )
        return self.distroless_tz_fr(ctr)

    @function
    def distroless_debian(self) -> dagger.Container:
        """Distroless static with Europe/Paris timezone."""
        ctr = dag.container().from_(
            f"gcr.io/distroless/static-debian{self.debian_version}"
        )
        return self.distroless_tz_fr(ctr)

    @function
    def pip_tools(self) -> dagger.Container:
        """Python 3.8 Alpine with pip-tools and a default user."""
        ctr = dag.container().from_("python:3.8-alpine")
        ctr = self.use_user(ctr)
        return ctr.with_exec(["pip", "--quiet", "install", "pip-tools"])

    @function
    def flask_venv(self, packages: str = "") -> dagger.Directory:
        """Debian python user venv with flask, exported as directory artifact."""
        ctr = self.debian_python_user_venv(packages=f"flask {packages}".strip())
        return ctr.directory("/app/venv")

    # ── Docker-in-Docker ────────────────────────────────────────────────

    @function
    def dind_container(
        self,
        base: dagger.Container | None = None,
    ) -> dagger.Container:
        """Return a container with Docker installed, ready for DinD.

        If base is provided, Docker is installed into it (must be Debian/Ubuntu-based).
        Otherwise uses ubuntu:24.04.
        """
        if base is None:
            base = dag.container().from_("ubuntu:24.04")

        return (
            base
            .with_exec(["apt-get", "update"])
            .with_exec([
                "apt-get", "install", "--yes",
                "ca-certificates", "curl", "gnupg", "iptables",
            ])
            .with_exec(["bash", "-c",
                         "install -m 0755 -d /etc/apt/keyrings"
                         " && curl -fsSL https://download.docker.com/linux/ubuntu/gpg"
                         " -o /etc/apt/keyrings/docker.asc"
                         " && chmod a+r /etc/apt/keyrings/docker.asc"
                         ' && echo "deb [arch=$(dpkg --print-architecture)'
                         " signed-by=/etc/apt/keyrings/docker.asc]"
                         " https://download.docker.com/linux/ubuntu"
                         ' $(. /etc/os-release && echo $VERSION_CODENAME) stable"'
                         " > /etc/apt/sources.list.d/docker.list"
                         " && apt-get update"
                         " && apt-get install --yes docker-ce docker-ce-cli containerd.io"])
        )

    @function
    def dind_with_docker(
        self,
        ctr: dagger.Container,
        cmd: str,
    ) -> dagger.Container:
        """Run a shell command inside the container with dockerd available.

        Handles cgroup v2 setup, tmpfs for /var/lib/docker,
        and dockerd lifecycle. The container must have Docker installed
        (use .dind_container() to prepare it). Runs with insecure_root_capabilities.
        """
        shell_cmd = _CGROUP_SETUP + _DOCKERD_START + cmd
        return ctr.with_exec(
            ["bash", "-c", shell_cmd],
            insecure_root_capabilities=True,
        )
