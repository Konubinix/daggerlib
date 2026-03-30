import dagger
from dagger import dag, function, object_type


CGROUP_SETUP = (
    "mount -t cgroup2 cgroup2 /sys/fs/cgroup 2>/dev/null || true\n"
    "mkdir -p /sys/fs/cgroup/init\n"
    "xargs -rn1 < /sys/fs/cgroup/cgroup.procs > /sys/fs/cgroup/init/cgroup.procs 2>/dev/null || true\n"
    "sed -e 's/ / +/g' -e 's/^/+/' < /sys/fs/cgroup/cgroup.controllers"
    " > /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null || true\n"
)

DOCKERD_START = (
    "mkdir -p /var/lib/docker\n"
    "mount -t tmpfs tmpfs /var/lib/docker\n"
    "dockerd &>/var/log/dockerd.log &\n"
    "sleep 3\n"
)


@object_type
class Dind:
    @function
    def container(
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
    def with_docker(
        self,
        ctr: dagger.Container,
        cmd: str,
    ) -> dagger.Container:
        """Run a shell command inside the container with dockerd available.

        Handles cgroup v2 setup, tmpfs for /var/lib/docker,
        and dockerd lifecycle. The container must have Docker installed
        (use .container() to prepare it). Runs with insecure_root_capabilities.
        """
        shell_cmd = CGROUP_SETUP + DOCKERD_START + cmd
        return ctr.with_exec(
            ["bash", "-c", shell_cmd],
            insecure_root_capabilities=True,
        )
