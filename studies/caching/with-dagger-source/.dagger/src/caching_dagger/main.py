# [[file:../../../../readme.org::*Sub-project: =.dagger= layout][Sub-project: =.dagger= layout:5]]
import time
from typing import Annotated

import dagger
from dagger import DefaultPath, Ignore, dag, function, object_type


@object_type
class CachingDagger:
    @function
    async def old_way(self) -> str:
        """Filter source inside the function. Returns elapsed seconds."""
        src = dag.directory().with_directory(
            ".",
            dag.current_module().source(),
            include=["data.txt"],
        )
        start = time.monotonic()
        await (
            dag.container()
            .from_("alpine:latest")
            .with_directory("/work", src)
            .with_exec(["sh", "-c", "sleep 3 && echo old"])
            .stdout()
        )
        return f"{time.monotonic() - start:.2f}s"

    @function
    async def new_way(
        self,
        src: Annotated[
            dagger.Directory,
            DefaultPath("."),
            Ignore(["**", "!data.txt"]),
        ],
    ) -> str:
        """Filter source at the engine level. Returns elapsed seconds."""
        start = time.monotonic()
        await (
            dag.container()
            .from_("alpine:latest")
            .with_directory("/work", src)
            .with_exec(["sh", "-c", "sleep 3 && echo new"])
            .stdout()
        )
        return f"{time.monotonic() - start:.2f}s"


# Sub-project: =.dagger= layout:5 ends here
