# [[file:../distroless.org::+begin_src python :tangle lib/distroless.py :noweb yes][No heading:1]]
import dagger
from dagger import dag, function


class DistrolessMixin:
    @function
    def distroless_set_tz(self, ctr: dagger.Container) -> dagger.Container:
        """Copy timezone artifacts into a distroless container (uses Lib.timezone)."""
        tz = self.alpine_tz()
        return ctr.with_file("/etc/localtime", tz.file("localtime")).with_file(
            "/etc/timezone", tz.file("timezone")
        )

    @function
    def distroless_python3_debian(self) -> dagger.Container:
        """Distroless python3 with timezone set."""
        ctr = dag.container().from_(
            f"gcr.io/distroless/python3-debian{self.debian_version}"
        )
        return self.distroless_set_tz(ctr)

    @function
    def distroless_debian(self) -> dagger.Container:
        """Distroless static with timezone set."""
        ctr = dag.container().from_(
            f"gcr.io/distroless/static-debian{self.debian_version}"
        )
        return self.distroless_set_tz(ctr)


# No heading:1 ends here
