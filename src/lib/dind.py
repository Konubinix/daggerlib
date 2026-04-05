# [[file:../dind.org::+begin_src python][No heading:2]]
import dagger
from dagger import dag, function


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
# No heading:2 ends here


# [[file:../dind.org::*Preparing a DinD-capable container][Preparing a DinD-capable container:1]]
@function
def dind_container(
    self,
    base: dagger.Container | None = None,
) -> dagger.Container:
    """Return a container with Docker installed, ready for DinD.

    If base is provided, Docker is installed into it (must be Debian/Ubuntu-based).
    Otherwise uses the image from Lib.dind_ubuntu_image.
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
                " && apt-get install --yes docker-ce docker-ce-cli containerd.io",
            ]
        )
    )


# Preparing a DinD-capable container:1 ends here


# [[file:../dind.org::*Running commands with dockerd][Running commands with dockerd:1]]
@function
def dind_with_docker(
    self,
    cmd: str,
    ctr: dagger.Container | None = None,
) -> dagger.Container:
    """Run a shell command inside the container with dockerd available.

    Handles cgroup v2 setup, tmpfs for /var/lib/docker,
    and dockerd lifecycle. If no container is provided, uses dind_container().
    Runs with insecure_root_capabilities.
    """
    if ctr is None:
        ctr = self.dind_container()
    shell_cmd = _CGROUP_SETUP + _DOCKERD_START + cmd
    return ctr.with_exec(
        ["bash", "-c", shell_cmd],
        insecure_root_capabilities=True,
    )


# Running commands with dockerd:1 ends here
