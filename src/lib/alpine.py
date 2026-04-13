# [[file:../alpine.org::+begin_src python :tangle lib/alpine.py :noweb yes][No heading:1]]
import dagger
from dagger import dag, function


class AlpineMixin:
    @function
    def alpine_set_tz(self, ctr: dagger.Container) -> dagger.Container:
        """Set timezone on an Alpine container (uses Lib.timezone)."""
        tz = self.timezone
        return ctr.with_exec(
            [
                "sh",
                "-c",
                "apk --quiet add --update tzdata"
                f" && cp /usr/share/zoneinfo/{tz} /etc/localtime"
                f' && echo "{tz}" > /etc/timezone'
                " && apk --quiet del tzdata",
            ]
        )

    @function
    def alpine(self, distro_packages: list[str] = ()) -> dagger.Container:
        """Alpine with timezone set and optional extra packages."""
        ctr = dag.container().from_(f"alpine:{self.alpine_version}")
        ctr = self.alpine_set_tz(ctr)
        if distro_packages:
            ctr = ctr.with_exec(["apk", "--quiet", "add"] + list(distro_packages))
        return ctr

    @function
    def alpine_user(
        self,
        distro_packages: list[str] = (),
        groups: list[str] = (),
        uid: int = 1000,
    ) -> dagger.Container:
        """Alpine with a default user."""
        ctr = self.alpine(distro_packages=distro_packages)
        return self.use_user(ctr, uid=uid, groups=groups)

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
    def alpine_python(self, distro_packages: list[str] = ()) -> dagger.Container:
        """Alpine with python3 and pip."""
        return self.alpine(
            distro_packages=["python3", "py3-pip"] + list(distro_packages)
        )

    @function
    def alpine_python_user_venv(
        self,
        distro_packages: list[str] = (),
        groups: list[str] = (),
        pip_packages: list[str] = (),
        work_dir: str = "/app",
    ) -> dagger.Container:
        """Alpine with python, user, and a virtualenv."""
        ctr = self.alpine_python(distro_packages=distro_packages)
        return self.python_user_venv(
            ctr, groups=groups, pip_packages=pip_packages, work_dir=work_dir
        )


# No heading:1 ends here
