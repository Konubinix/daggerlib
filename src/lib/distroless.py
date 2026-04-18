# [[file:../distroless.org::+begin_src python :tangle lib/distroless.py :noweb yes :exports none][No heading:1]]
import dagger
from dagger import dag, function


class DistrolessMixin:

    @function
    def distroless_set_tz(self, ctr: dagger.Container) -> dagger.Container:
        """Copy timezone artifacts into a distroless container (uses Lib.timezone)."""
        tz = self.alpine_tz()
        return (
            ctr
            .with_file("/etc/localtime", tz.file("localtime"))
            .with_file("/etc/timezone", tz.file("timezone"))
        )

    @function
    def distroless_python3_debian(self) -> dagger.Container:
        """Distroless python3 with timezone set."""
        ctr = dag.container().from_(self.pinned(self._distroless_python3_image))
        return self.distroless_set_tz(ctr)

    @function
    def distroless_debian(self) -> dagger.Container:
        """Distroless static with timezone set."""
        ctr = dag.container().from_(self.pinned(self._distroless_static_image))
        return self.distroless_set_tz(ctr)

    @property
    def _distroless_python3_image(self) -> str:
        return f"gcr.io/distroless/python3-debian{self.debian_version}"

    @property
    def _distroless_static_image(self) -> str:
        return f"gcr.io/distroless/static-debian{self.debian_version}"
# No heading:1 ends here
