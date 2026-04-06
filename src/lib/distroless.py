# [[file:../distroless.org::+begin_src python][No heading:1]]
import dagger
from dagger import dag, function
# No heading:1 ends here


# [[file:../distroless.org::*Setting the timezone on distroless][Setting the timezone on distroless:1]]
@function
def distroless_set_tz(self, ctr: dagger.Container) -> dagger.Container:
    """Copy timezone artifacts into a distroless container (uses Lib.timezone)."""
    tz = self.alpine_tz()
    return ctr.with_file("/etc/localtime", tz.file("localtime")).with_file(
        "/etc/timezone", tz.file("timezone")
    )


# Setting the timezone on distroless:1 ends here


# [[file:../distroless.org::*Distroless Python 3][Distroless Python 3:1]]
@function
def distroless_python3_debian(self) -> dagger.Container:
    """Distroless python3 with timezone set."""
    ctr = dag.container().from_(
        f"gcr.io/distroless/python3-debian{self.debian_version}"
    )
    return self.distroless_set_tz(ctr)


# Distroless Python 3:1 ends here


# [[file:../distroless.org::*Distroless static][Distroless static:1]]
@function
def distroless_debian(self) -> dagger.Container:
    """Distroless static with timezone set."""
    ctr = dag.container().from_(f"gcr.io/distroless/static-debian{self.debian_version}")
    return self.distroless_set_tz(ctr)


# Distroless static:1 ends here
