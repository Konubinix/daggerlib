# [[file:../../../readme.org::+begin_src python :tangle .dagger/src/data_pipeline/main.py :noweb yes][No heading:5]]
from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function, object_type


@object_type
class DataPipeline:
    @function
    async def transform(self, src: Annotated[dagger.Directory, DefaultPath(".")]) -> str:
        """Run the CSV transform in a clean Alpine container."""
        return await (
            dag.lib().alpine_python_user_venv()
            .with_file('/app/transform.py', src.file('transform.py'))
            .with_file('/app/sample.csv', src.file('sample.csv'))
            .with_exec(['sh', '-c', 'python3 transform.py < sample.csv'])
            .stdout()
        )
    @function
    async def check_requests(self) -> str:
        """Verify requests is installed in the venv."""
        return await (
            dag.lib().alpine_python_user_venv(pip_packages=['requests'])
            .with_exec(['python3', '-c', 'import requests; print(requests.__version__)'])
            .stdout()
        )
    @function
    async def transform_debian(self, src: Annotated[dagger.Directory, DefaultPath(".")]) -> str:
        """Run the same transform on Debian for native library compatibility."""
        return await (
            dag.lib().debian_python_user_venv()
            .with_file('/app/transform.py', src.file('transform.py'))
            .with_file('/app/sample.csv', src.file('sample.csv'))
            .with_exec(['sh', '-c', 'python3 transform.py < sample.csv'])
            .stdout()
        )
    @function
    async def pip_lock(self, src: Annotated[dagger.Directory, DefaultPath(".")]) -> str:
        """Lock dependencies with pip-compile."""
        return await (
            dag.lib().pip_tools()
            .with_file('/home/sam/requirements.in', src.file('requirements.in'))
            .with_exec(['sh', '-c', 'pip-compile --quiet requirements.in && head -5 requirements.txt'])
            .stdout()
        )
# No heading:5 ends here
