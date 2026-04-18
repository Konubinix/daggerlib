# [[file:../python.org::+begin_src python :tangle lib/python.py :noweb yes :exports none][No heading:1]]
import dagger
from dagger import function


class PythonMixin:

    @function
    def python_venv(
        self,
        ctr: dagger.Container,
        base: str,
        pip_packages: list[str] = (),
    ) -> dagger.Container:
        """Create a Python venv with --system-site-packages and optionally install packages."""
        ctr = ctr.with_exec([
            "python3", "-m", "venv", "--system-site-packages", f"{base}/venv",
        ]).with_env_variable("PATH", f"{base}/venv/bin:$PATH", expand=True)
        if pip_packages:
            ctr = ctr.with_exec(
                [f"{base}/venv/bin/python", "-m", "pip", "--quiet", "install", "--upgrade"]
                + list(pip_packages)
            )
        return ctr

    @function
    def python_user_venv(
        self,
        ctr: dagger.Container,
        groups: list[str] = (),
        pip_packages: list[str] = (),
        work_dir: str = "/app",
    ) -> dagger.Container:
        """Add a user, workdir, and virtualenv to a container that already has Python."""
        ctr = self.use_user(ctr, groups=groups)
        ctr = ctr.with_workdir(work_dir)
        return self.python_venv(ctr, base=work_dir, pip_packages=pip_packages)
# No heading:1 ends here
