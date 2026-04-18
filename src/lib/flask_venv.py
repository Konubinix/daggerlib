# [[file:../flask_venv.org::+begin_src python :tangle lib/flask_venv.py :noweb yes :exports none][No heading:1]]
import dagger
from dagger import function


class FlaskMixin:

    @function
    def flask_venv(self, pip_packages: list[str] = ()) -> dagger.Directory:
        """Debian python user venv with flask, exported as directory artifact."""
        ctr = self.debian_python_user_venv(pip_packages=["flask"] + list(pip_packages))
        return ctr.directory("/app/venv")
# No heading:1 ends here
