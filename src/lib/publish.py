# [[file:../publish.org::+begin_src python :tangle lib/publish.py :noweb yes :exports none][No heading:1]]
import dagger
from dagger import dag, function


class PublishMixin:

    @function
    async def publish(
        self,
        variants: list[dagger.Container],
        address: str,
        registry_service: dagger.Service | None = None,
    ) -> str:
        """Publish VARIANTS as one multi-arch image at ADDRESS."""
        ctr = dag.container()
        if registry_service is not None:
            return await ctr.publish(
                address, platform_variants=variants, registry_service=registry_service,
            )
        return await ctr.publish(address, platform_variants=variants)

    @function
    async def publish_roundtrip(self) -> str:
        """Push a two-arch image to a throwaway registry and read both arches back."""
        platforms = ("linux/amd64", "linux/arm64")
        registry = (
            dag.container()
            .from_(self.pinned(self._registry_image))
            .with_exposed_port(5000)
            .as_service()
        )
        variants = [
            dag.container(platform=dagger.Platform(p)).from_(self.pinned(self._alpine_image))
            for p in platforms
        ]
        addr = "localhost:5000/probe:t"
        await self.publish(variants, addr, registry_service=registry)
        for p in platforms:
            release = await (
                dag.container(platform=dagger.Platform(p))
                .from_(addr, registry_service=registry)
                .file("/etc/alpine-release")
                .contents()
            )
            if not release.strip():
                return f"empty:{p}"
        return "ok"

    @property
    def _registry_image(self) -> str:
        return "registry:2"
# No heading:1 ends here
