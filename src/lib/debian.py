# [[file:../debian.org::+begin_src python][No heading:1]]
import shlex

import dagger
from dagger import dag, function
# No heading:1 ends here


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
def debian_set_tz(self, ctr: dagger.Container) -> dagger.Container:
    """Set timezone on a Debian container (uses Lib.timezone)."""
    return ctr.with_exec(["rm", "/etc/localtime"]).with_exec(
        ["ln", "-sf", f"/usr/share/zoneinfo/{self.timezone}", "/etc/localtime"]
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
    """Debian slim with timezone set, no auto-install, and optional extra packages."""
    ctr = dag.container().from_(f"debian:{self.debian_tag}")
    ctr = self.debian_no_auto_install(ctr)
    ctr = self.debian_set_tz(ctr)
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
    return self.python_user_venv(
        ctr, groups=groups, packages=packages, work_dir=work_dir
    )


# Python with a user and virtualenv on Debian:1 ends here


# [[file:../debian.org::*Extracting the localtime file][Extracting the localtime file:1]]
@function
def debian_localtime(self) -> dagger.File:
    """Extract the localtime file from a Debian container."""
    return self.debian().file("/etc/localtime")


# Extracting the localtime file:1 ends here
