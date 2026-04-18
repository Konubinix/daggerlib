# [[file:../../../readme.org::+begin_src python :tangle .dagger/src/ci_like_production/main.py :noweb yes][No heading:3]]
import dagger
from dagger import dag, function, object_type


@object_type
class CiLikeProduction:
    @function
    async def whoami_check(self) -> str:
        """Check that the container runs as a regular user."""
        return await (
            dag.lib().alpine_user()
            .with_exec(['whoami'])
            .stdout()
        )
    @function
    async def home_check(self) -> str:
        """Check the user has a real home directory."""
        return await (
            dag.lib().alpine_user()
            .with_exec(['pwd'])
            .stdout()
        )
    @function
    async def uid_check(self) -> str:
        """Check the user has UID 1000."""
        return await (
            dag.lib().alpine_user()
            .with_exec(['id', 'sam'])
            .stdout()
        )
    @function
    async def debian_uid_check(self) -> str:
        """Check the Debian user has UID 1000."""
        return await (
            dag.lib().debian_user()
            .with_exec(['id', 'sam'])
            .stdout()
        )
# No heading:3 ends here
