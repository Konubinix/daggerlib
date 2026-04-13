# [[file:../debian.org::+begin_src python :tangle lib/debian.py :noweb yes][No heading:1]]
import shlex

import dagger
from dagger import dag, function


class DebianMixin:
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

    @function
    def debian_set_tz(self, ctr: dagger.Container) -> dagger.Container:
        """Set timezone on a Debian container (uses Lib.timezone)."""
        return ctr.with_exec(["rm", "/etc/localtime"]).with_exec(
            ["ln", "-sf", f"/usr/share/zoneinfo/{self.timezone}", "/etc/localtime"]
        )

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

    @function
    def debian(self, distro_packages: list[str] = ()) -> dagger.Container:
        """Debian slim with timezone set, no auto-install, and optional extra packages."""
        ctr = dag.container().from_(f"debian:{self.debian_tag}")
        ctr = self.debian_no_auto_install(ctr)
        ctr = self.debian_set_tz(ctr)
        if distro_packages:
            packages_str = shlex.join(distro_packages)
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

    @function
    def debian_user(self, distro_packages: list[str] = ()) -> dagger.Container:
        """Debian with a default user."""
        ctr = self.debian(distro_packages=distro_packages)
        return self.use_user(ctr)

    @function
    def debian_python_user_venv(
        self,
        distro_packages: list[str] = (),
        groups: list[str] = (),
        pip_packages: list[str] = (),
        work_dir: str = "/app",
    ) -> dagger.Container:
        """Debian with python, user, and a virtualenv."""
        ctr = self.debian(distro_packages=["python3-venv"] + list(distro_packages))
        return self.python_user_venv(
            ctr, groups=groups, pip_packages=pip_packages, work_dir=work_dir
        )

    @function
    def debian_localtime(self) -> dagger.File:
        """Extract the localtime file from a Debian container."""
        return self.debian().file("/etc/localtime")


# No heading:1 ends here
