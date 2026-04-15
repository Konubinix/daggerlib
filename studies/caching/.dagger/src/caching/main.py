# [[file:../../../readme.org::*The module][The module:3]]
import time
from typing import Annotated

import dagger
from dagger import DefaultPath, Ignore, dag, function, object_type


def _dir_a() -> dagger.Directory:
    return dag.directory().with_new_file("data.txt", "hello")


def _dir_b() -> dagger.Directory:
    return (
        dag.directory()
        .with_new_file("data.txt", "hello")
        .with_new_file("junk.txt", "junk")
        .without_file("junk.txt")
    )


@object_type
class Caching:
    @function
    async def prove_identical(self) -> str:
        """Show that dir_a and dir_b have the same content digest but different container IDs."""
        dir_a = _dir_a()
        dir_b = _dir_b()

        digest_a = await dir_a.digest()
        digest_b = await dir_b.digest()

        ctr = dag.container().from_("alpine:latest")

        ctr_a = ctr.with_directory("/work", dir_a)
        ctr_b = ctr.with_directory("/work", dir_b)
        ctr_c = ctr.with_directory("/work", dir_a)

        # Attempt to flatten the graph
        dir_b_synced = await dir_b.sync()
        ctr_b_synced = ctr.with_directory("/work", dir_b_synced)

        dir_b_copied = dag.directory().with_directory(".", dir_b)
        ctr_b_copied = ctr.with_directory("/work", dir_b_copied)

        dir_b_roundtrip = (
            dag.container()
            .from_("alpine:latest")
            .with_directory("/work", dir_b)
            .directory("/work")
        )
        ctr_b_roundtrip = ctr.with_directory("/work", dir_b_roundtrip)

        id_a = await ctr_a.id()
        id_b = await ctr_b.id()
        id_c = await ctr_c.id()
        id_b_synced = await ctr_b_synced.id()
        id_b_copied = await ctr_b_copied.id()
        id_b_roundtrip = await ctr_b_roundtrip.id()

        return (
            f"dir digests identical: {digest_a == digest_b}\n"
            f"\n"
            f"a vs b (different graph, same content): {id_a == id_b}\n"
            f"a vs c (same graph):                    {id_a == id_c}\n"
            f"\n"
            f"flattening attempts (all should be True to fix caching):\n"
            f"  sync():                {id_a == id_b_synced}\n"
            f"  copy via with_directory: {id_a == id_b_copied}\n"
            f"  roundtrip via container: {id_a == id_b_roundtrip}"
        )

    @function
    async def cached(self, run: int = 0) -> str:
        """Mount dir_a and run a slow command. Returns withExec elapsed seconds."""
        start = time.monotonic()
        await (
            dag.container()
            .from_("alpine:latest")
            .with_directory("/work", _dir_a())
            .with_exec(["sh", "-c", "sleep 3 && echo done"])
            .stdout()
        )
        return f"{time.monotonic() - start:.2f}s"

    @function
    async def busted(self, run: int = 0) -> str:
        """Mount dir_b (same content, different operation graph). Returns withExec elapsed seconds."""
        start = time.monotonic()
        await (
            dag.container()
            .from_("alpine:latest")
            .with_directory("/work", _dir_b())
            .with_exec(["sh", "-c", "sleep 3 && echo done"])
            .stdout()
        )
        return f"{time.monotonic() - start:.2f}s"


# The module:3 ends here
