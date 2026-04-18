# [[file:../pins.org::+begin_src python :tangle lib/pins.py :noweb yes :exports none][No heading:1]]
import json
from pathlib import Path

import dagger
from dagger import dag, function


_PINS_FILE = Path(__file__).resolve().parent.parent.parent / "image-pins.json"


def _load_pins() -> dict[str, str]:
    if _PINS_FILE.exists():
        return json.loads(_PINS_FILE.read_text())
    return {}


class PinsMixin:

    def pinned(self, tag: str) -> str:
        """Return tag@digest if pinned, else bare tag."""
        digest = _load_pins().get(tag)
        if digest:
            return f"{tag}@{digest}"
        return tag

    def _image_tags(self) -> list[str]:
        tags = []
        for name in sorted(dir(type(self))):
            if name.endswith("_image") and name.startswith("_") and name != "_image":
                value = getattr(type(self), name)
                if isinstance(value, property):
                    tags.append(getattr(self, name))
        return tags

    @function
    async def upgrade_pins(self) -> dagger.File:
        """Resolve all image tags to their current digests and return image-pins.json."""
        ctr = (
            dag.container()
            .from_(self.pinned("cgr.dev/chainguard/crane:latest"))
            .with_entrypoint([])
        )
        pins: dict[str, str] = {}
        for tag in self._image_tags():
            digest = await ctr.with_exec(["crane", "digest", tag]).stdout()
            pins[tag] = digest.strip()
        content = json.dumps(pins, indent=2) + "\n"
        return dag.directory().with_new_file("image-pins.json", content).file("image-pins.json")
# No heading:1 ends here
