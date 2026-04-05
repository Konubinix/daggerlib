# [[file:../debian.org::+begin_src python][No heading:2]]
import shlex

import dagger
from dagger import dag, function
# No heading:2 ends here


# [[file:../debian.org::*Disabling automatic recommends][Disabling automatic recommends:1]]
@function
def debian_no_auto_install(self, ctr: dagger.Container) -> dagger.Container:
    """Disable apt recommends and suggests."""
    return ctr.with_exec(
        [
            "sh",
            "-c",
            "echo 'APT::Install-Recommends \"0\";' > /etc/apt/apt.conf.d/01norecommend"
            " && "
            "echo 'APT::Install-Suggests \"0\";' >> /etc/apt/apt.conf.d/01norecommend",
        ]
    )


# Disabling automatic recommends:1 ends here


# [[file:../debian.org::*Setting the timezone on Debian][Setting the timezone on Debian:1]]
@function
def debian_tz_fr(self, ctr: dagger.Container) -> dagger.Container:
    """Set timezone to Europe/Paris on a Debian container."""
    return ctr.with_exec(["rm", "/etc/localtime"]).with_exec(
        ["ln", "-sf", "/usr/share/zoneinfo/Europe/Paris", "/etc/localtime"]
    )


# Setting the timezone on Debian:1 ends here


# [[file:../debian.org::*Cleaning up apt caches][Cleaning up apt caches:1]]
@function
def debian_apt_cleanup(self, ctr: dagger.Container) -> dagger.Container:
    """Clean apt caches."""
    return ctr.with_exec(
        [
            "sh",
            "-c",
            "apt-get --quiet clean && rm -rf /var/lib/apt/lists/*",
        ]
    )


# Cleaning up apt caches:1 ends here


# [[file:../debian.org::*A base Debian container][A base Debian container:1]]
@function
def debian(self, extra_packages: list[str] = ()) -> dagger.Container:
    """Debian slim with Europe/Paris timezone, no auto-install, and optional extra packages."""
    tag = f"{self.debian_version}.{self.debian_min_version}-slim"
    ctr = dag.container().from_(f"debian:{tag}")
    ctr = self.debian_no_auto_install(ctr)
    ctr = self.debian_tz_fr(ctr)
    if extra_packages:
        packages_str = " ".join(shlex.quote(p) for p in extra_packages)
        ctr = ctr.with_exec(
            [
                "sh",
                "-c",
                "{ apt-get --quiet update"
                f" && apt-get --quiet install --yes {packages_str}"
                " ; } > /tmp/log 2>&1 || { cat /tmp/log; exit 1; }",
            ]
        )
        ctr = self.debian_apt_cleanup(ctr)
    return ctr


# A base Debian container:1 ends here


# [[file:../debian.org::*Debian with a default user][Debian with a default user:1]]
@function
def debian_user(self, extra_packages: list[str] = ()) -> dagger.Container:
    """Debian with a default user."""
    ctr = self.debian(extra_packages=extra_packages)
    return self.use_user(ctr)


# Debian with a default user:1 ends here


# [[file:../debian.org::*Python with a user and virtualenv on Debian][Python with a user and virtualenv on Debian:1]]
@function
def debian_python_user_venv(
    self,
    extra_packages: list[str] = (),
    groups: list[str] = (),
    packages: list[str] = (),
    work_dir: str = "/app",
) -> dagger.Container:
    """Debian with python, user, and a virtualenv."""
    ctr = self.debian(extra_packages=["python3-venv"] + list(extra_packages))
    ctr = self.use_user(ctr, groups=groups)
    ctr = ctr.with_workdir(work_dir)
    return self.python_venv(ctr, base=work_dir, packages=packages)


# Python with a user and virtualenv on Debian:1 ends here


# [[file:../debian.org::*Extracting the Europe/Paris timezone file][Extracting the Europe/Paris timezone file:1]]
@function
def debian_europe_paris(self) -> dagger.File:
    """Extract the Europe/Paris localtime file from Debian."""
    tag = f"{self.debian_version}.{self.debian_min_version}-slim"
    return (
        dag.container().from_(f"debian:{tag}").file("/usr/share/zoneinfo/Europe/Paris")
    )


# Extracting the Europe/Paris timezone file:1 ends here


# [[file:../debian.org::*Creating a Python venv][Creating a Python venv:1]]
@function
def python_venv(
    self,
    ctr: dagger.Container,
    base: str,
    packages: list[str] = (),
) -> dagger.Container:
    """Create a Python venv with --system-site-packages and optionally install packages."""
    ctr = ctr.with_exec(
        [
            "python3",
            "-m",
            "venv",
            "--system-site-packages",
            f"{base}/venv",
        ]
    ).with_env_variable("PATH", f"{base}/venv/bin:$PATH", expand=True)
    if packages:
        ctr = ctr.with_exec(
            [f"{base}/venv/bin/python", "-m", "pip", "--quiet", "install", "--upgrade"]
            + list(packages)
        )
    return ctr


# Creating a Python venv:1 ends here
