# [[file:../alpine.org::+begin_src python][No heading:1]]
import dagger
from dagger import dag, function
# No heading:1 ends here


# [[file:../alpine.org::*Setting the timezone on Alpine][Setting the timezone on Alpine:1]]
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


# Setting the timezone on Alpine:1 ends here


# [[file:../alpine.org::*A base Alpine container with optional extra packages][A base Alpine container with optional extra packages:1]]
@function
def alpine(self, extra_packages: list[str] = ()) -> dagger.Container:
    """Alpine with timezone set and optional extra packages."""
    ctr = dag.container().from_(f"alpine:{self.alpine_version}")
    ctr = self.alpine_set_tz(ctr)
    if extra_packages:
        ctr = ctr.with_exec(["apk", "--quiet", "add"] + list(extra_packages))
    return ctr


# A base Alpine container with optional extra packages:1 ends here


# [[file:../alpine.org::*A non-root user for safer workflows][A non-root user for safer workflows:1]]
@function
def alpine_user(
    self,
    extra_packages: list[str] = (),
    groups: list[str] = (),
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
def alpine_python(self, extra_packages: list[str] = ()) -> dagger.Container:
    """Alpine with python3 and pip."""
    return self.alpine(extra_packages=["python3", "py3-pip"] + list(extra_packages))


# Python on Alpine:1 ends here


# [[file:../alpine.org::*Python with a user and virtualenv][Python with a user and virtualenv:1]]
@function
def alpine_python_user_venv(
    self,
    extra_packages: list[str] = (),
    groups: list[str] = (),
    packages: list[str] = (),
    work_dir: str = "/app",
) -> dagger.Container:
    """Alpine with python, user, and a virtualenv."""
    ctr = self.alpine_python(extra_packages=extra_packages)
    return self.python_user_venv(
        ctr, groups=groups, packages=packages, work_dir=work_dir
    )


# Python with a user and virtualenv:1 ends here
