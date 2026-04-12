# [[file:../../TECHNICAL.org::*Module entry point][Module entry point:2]]
"""Reusable container helpers: base images, timezone, user setup, DinD, etc."""

from dagger import function, object_type

from .alpine import (
    alpine,
    alpine_python,
    alpine_python_user_venv,
    alpine_set_tz,
    alpine_tz,
    alpine_user,
)
from .debian import (
    debian,
    debian_apt_cleanup,
    debian_localtime,
    debian_no_auto_install,
    debian_python_user_venv,
    debian_set_tz,
    debian_user,
)
from .python import python_user_venv, python_venv
from .dind import (
    dind_container,
    dind_emacs_container,
    dind_init_examples,
    dind_run_org,
    dind_run_tests,
    dind_tangle,
    dind_with_docker,
    emacs_container,
    export_html,
)
from .distroless import distroless_debian, distroless_python3_debian, distroless_set_tz
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
    timezone: str = "Europe/Paris"
    dind_ubuntu_image: str = "ubuntu:24.04"

    # Alpine
    alpine_set_tz = alpine_set_tz
    alpine = alpine
    alpine_user = alpine_user
    alpine_tz = alpine_tz
    alpine_python = alpine_python
    alpine_python_user_venv = alpine_python_user_venv

    # Debian
    @property
    def debian_tag(self) -> str:
        return f"{self.debian_version}.{self.debian_min_version}-slim"

    debian_no_auto_install = debian_no_auto_install
    debian_set_tz = debian_set_tz
    debian_apt_cleanup = debian_apt_cleanup
    debian = debian
    debian_user = debian_user
    debian_python_user_venv = debian_python_user_venv
    debian_localtime = debian_localtime

    # Python
    python_venv = python_venv
    python_user_venv = python_user_venv

    # Distroless
    distroless_set_tz = distroless_set_tz
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

    # Emacs container (lightweight, no Docker)
    emacs_container = emacs_container

    # DinD
    dind_container = dind_container
    dind_emacs_container = dind_emacs_container
    dind_with_docker = dind_with_docker
    dind_run_tests = dind_run_tests
    dind_run_org = dind_run_org
    dind_tangle = dind_tangle
    dind_init_examples = dind_init_examples
    export_html = export_html

    # Ralph
    ralph = ralph


# Module entry point:2 ends here
