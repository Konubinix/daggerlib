# [[file:../flask_venv.org::+begin_src python][No heading:1]]
import dagger
from dagger import function
# No heading:1 ends here


# [[file:../flask_venv.org::*A Flask virtualenv as a directory artifact][A Flask virtualenv as a directory artifact:1]]
@function
def flask_venv(self, packages: list[str] = ()) -> dagger.Directory:
    """Debian python user venv with flask, exported as directory artifact."""
    ctr = self.debian_python_user_venv(packages=["flask"] + list(packages))
    return ctr.directory("/app/venv")


# A Flask virtualenv as a directory artifact:1 ends here
