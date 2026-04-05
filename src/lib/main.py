# [[file:../../TECHNICAL.org::*Module entry point][Module entry point:2]]
"""Reusable container helpers: base images, timezone, user setup, DinD, etc."""

from dagger import function, object_type

from .dev import Dev
from .alpine import (
    alpine,
    alpine_python,
    alpine_python_user_venv,
    alpine_tz,
    alpine_tz_fr,
    alpine_user,
)
from .debian import (
    debian,
    debian_apt_cleanup,
    debian_europe_paris,
    debian_no_auto_install,
    debian_python_user_venv,
    debian_tz_fr,
    debian_user,
    python_venv,
)
from .dind import dind_container, dind_with_docker
from .distroless import distroless_debian, distroless_python3_debian, distroless_tz_fr
from .flask_venv import flask_venv
from .pip_tools import pip_tools
from .ralph import ralph
from .user import as_user, setup_user, use_user


@object_type
class Lib:
    alpine_version: str = "3.23"
    debian_version: str = "13"
    debian_min_version: str = "2"
    pip_tools_python_version: str = "3.12"
    default_username: str = "sam"
    dev_debian_image: str = "debian:bookworm-slim"

    # Alpine
    alpine_tz_fr = alpine_tz_fr
    alpine = alpine
    alpine_user = alpine_user
    alpine_tz = alpine_tz
    alpine_python = alpine_python
    alpine_python_user_venv = alpine_python_user_venv

    # Debian
    debian_no_auto_install = debian_no_auto_install
    debian_tz_fr = debian_tz_fr
    debian_apt_cleanup = debian_apt_cleanup
    debian = debian
    debian_user = debian_user
    debian_python_user_venv = debian_python_user_venv
    debian_europe_paris = debian_europe_paris
    python_venv = python_venv

    # Distroless
    distroless_tz_fr = distroless_tz_fr
    distroless_python3_debian = distroless_python3_debian
    distroless_debian = distroless_debian

    # User
    setup_user = setup_user
    as_user = as_user
    use_user = use_user

    # Pip tools
    pip_tools = pip_tools

    # Flask
    flask_venv = flask_venv

    # DinD
    dind_container = dind_container
    dind_with_docker = dind_with_docker

    # Ralph
    ralph = ralph

    @function
    def dev(self) -> Dev:
        """Development tooling: tangle, test, and run inside containers."""
        return Dev(debian_image=self.dev_debian_image)


# Module entry point:2 ends here
