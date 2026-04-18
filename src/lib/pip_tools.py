# [[file:../pip_tools.org::+begin_src python :tangle lib/pip_tools.py :noweb yes :exports none][No heading:1]]
import dagger
from dagger import dag, function


class PipToolsMixin:

    @function
    def pip_tools(self) -> dagger.Container:
        """Python Alpine with pip-tools and a default user."""
        ctr = dag.container().from_(self.pinned(self._pip_tools_image))
        ctr = self.use_user(ctr)
        return ctr.with_exec(["pip", "--quiet", "install", "pip-tools"])

    @property
    def _pip_tools_image(self) -> str:
        return f"python:{self.pip_tools_python_version}-alpine"
# No heading:1 ends here
