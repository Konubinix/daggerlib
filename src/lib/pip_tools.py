# [[file:../pip_tools.org::+begin_src python][No heading:1]]
import dagger
from dagger import dag, function
# No heading:1 ends here


# [[file:../pip_tools.org::*A pip-tools container][A pip-tools container:1]]
@function
def pip_tools(self) -> dagger.Container:
    """Python Alpine with pip-tools and a default user."""
    ctr = dag.container().from_(f"python:{self.pip_tools_python_version}-alpine")
    ctr = self.use_user(ctr)
    return ctr.with_exec(["pip", "--quiet", "install", "pip-tools"])


# A pip-tools container:1 ends here
