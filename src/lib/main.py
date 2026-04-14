# [[file:../../TECHNICAL.org::*Module entry point][Module entry point:2]]
"""Reusable container helpers: base images, timezone, user setup, DinD, etc."""

from dagger import object_type

from .alpine import AlpineMixin
from .debian import DebianMixin
from .dind import DindMixin
from .distroless import DistrolessMixin
from .flask_venv import FlaskMixin
from .pip_tools import PipToolsMixin
from .python import PythonMixin
from .ralph import RalphMixin
from .user import UserMixin


@object_type
class Lib(
    AlpineMixin,
    DebianMixin,
    DistrolessMixin,
    UserMixin,
    PythonMixin,
    DindMixin,
    FlaskMixin,
    PipToolsMixin,
    RalphMixin,
):
    alpine_version: str = "3.23"
    debian_version: str = "13"
    debian_min_version: str = "2"
    pip_tools_python_version: str = "3.12"
    default_username: str = "sam"
    timezone: str = "Europe/Paris"
    dind_ubuntu_image: str = "ubuntu:24.04"
    dind_image: str = "docker:27-dind"

    @property
    def debian_tag(self) -> str:
        return f"{self.debian_version}.{self.debian_min_version}-slim"


# Module entry point:2 ends here
