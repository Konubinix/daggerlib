# [[file:../../../readme.org::+begin_src python :tangle .dagger/src/log_collector/main.py :noweb yes][No heading:6]]
from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function, object_type


@object_type
class LogCollector:
    @function
    async def collect_on_alpine(self, src: Annotated[dagger.Directory, DefaultPath(".")]) -> str:
        """Run the log collector on Alpine."""
        return await (
            dag.lib().alpine_python_user_venv()
            .with_file('/app/collector.py', src.file('collector.py'))
            .with_directory('/app/logs', src.directory('logs'))
            .with_exec(['python3', 'collector.py', 'logs'])
            .stdout()
        )
    @function
    async def collect_on_debian(self, src: Annotated[dagger.Directory, DefaultPath(".")]) -> str:
        """Run the log collector on Debian."""
        return await (
            dag.lib().debian_python_user_venv()
            .with_file('/app/collector.py', src.file('collector.py'))
            .with_directory('/app/logs', src.directory('logs'))
            .with_exec(['python3', 'collector.py', 'logs'])
            .stdout()
        )
    @function
    async def collect_on_distroless(self, src: Annotated[dagger.Directory, DefaultPath(".")]) -> str:
        """Run the log collector on distroless."""
        return await (
            dag.lib().distroless_python3_debian()
            .with_file('/app/collector.py', src.file('collector.py'))
            .with_directory('/app/logs', src.directory('logs'))
            .with_exec(['python3', '/app/collector.py', '/app/logs'])
            .stdout()
        )
# No heading:6 ends here
