# [[file:../alpine.org::+begin_src python][No heading:2]]
import dagger
from dagger import dag, function
# No heading:2 ends here


# [[file:../alpine.org::*Setting the timezone on Alpine][Setting the timezone on Alpine:1]]
@function
def alpine_tz_fr(self, ctr: dagger.Container) -> dagger.Container:
    """Set timezone to Europe/Paris on an Alpine container."""
    return ctr.with_exec(
        [
            "sh",
            "-c",
            "apk --quiet add --update tzdata"
            " && cp /usr/share/zoneinfo/Europe/Paris /etc/localtime"
            ' && echo "Europe/Paris" > /etc/timezone'
            " && apk --quiet del tzdata",
        ]
    )


# Setting the timezone on Alpine:1 ends here


# [[file:../alpine.org::*A base Alpine container with optional extra packages][A base Alpine container with optional extra packages:1]]
@function
def alpine(self, extra_packages: str = "") -> dagger.Container:
    """Alpine with Europe/Paris timezone and optional extra packages."""
    ctr = dag.container().from_(f"alpine:{self.alpine_version}")
    ctr = self.alpine_tz_fr(ctr)
    if extra_packages:
        ctr = ctr.with_exec(
            [
                "sh",
                "-c",
                f"apk --quiet add {extra_packages}",
            ]
        )
    return ctr


# A base Alpine container with optional extra packages:1 ends here


# [[file:../alpine.org::*A non-root user for safer workflows][A non-root user for safer workflows:1]]
@function
def alpine_user(
    self,
    extra_packages: str = "",
    groups: str = "",
) -> dagger.Container:
    """Alpine with a default user."""
    ctr = self.alpine(extra_packages=extra_packages)
    return self.use_user(ctr, groups=groups)


# A non-root user for safer workflows:1 ends here


# [[file:../alpine.org::*Timezone artifacts for other containers][Timezone artifacts for other containers:1]]
@function
def alpine_tz(self) -> dagger.Directory:
    """Extract /etc/localtime and /etc/timezone from Alpine as artifacts."""
    ctr = self.alpine()
    return (
        dag.directory()
        .with_file("localtime", ctr.file("/etc/localtime"))
        .with_file("timezone", ctr.file("/etc/timezone"))
    )


# Timezone artifacts for other containers:1 ends here


# [[file:../alpine.org::*Python on Alpine][Python on Alpine:1]]
@function
def alpine_python(self, extra_packages: str = "") -> dagger.Container:
    """Alpine with python3 and pip."""
    return self.alpine(extra_packages=f"python3 py3-pip {extra_packages}".strip())


# Python on Alpine:1 ends here


# [[file:../alpine.org::*Python with a user and virtualenv][Python with a user and virtualenv:1]]
@function
def alpine_python_user_venv(
    self,
    extra_packages: str = "",
    groups: str = "",
    packages: str = "",
    work_dir: str = "/app",
) -> dagger.Container:
    """Alpine with python, user, and a virtualenv."""
    ctr = self.alpine_python(extra_packages=extra_packages)
    ctr = self.use_user(ctr, groups=groups)
    ctr = ctr.with_workdir(work_dir)
    return self.python_venv(ctr, base=work_dir, packages=packages)


# Python with a user and virtualenv:1 ends here
