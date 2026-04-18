# [[file:../../../readme.org::+begin_src python :tangle .dagger/src/webhook_receiver/main.py :noweb yes][No heading:4]]
from typing import Annotated

import dagger
from dagger import DefaultPath, dag, function, object_type


@object_type
class WebhookReceiver:
    @function
    async def flask_routes(self, src: Annotated[dagger.Directory, DefaultPath(".")]) -> str:
        """Verify the Flask app loads and exposes the expected routes."""
        return await (
            dag.lib().alpine_python_user_venv(pip_packages=['flask'])
            .with_file('/app/app.py', src.file('app.py'))
            .with_exec(['python3', '-c', "from app import app; print(sorted(r.rule for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>'))"])
            .stdout()
        )
    @function
    async def gunicorn_check(self, src: Annotated[dagger.Directory, DefaultPath(".")]) -> str:
        """Verify gunicorn can find the Flask app."""
        return await (
            dag.lib().alpine_python_user_venv(pip_packages=['flask', 'gunicorn'])
            .with_file('/app/app.py', src.file('app.py'))
            .with_exec(['gunicorn', '--check-config', 'app:app'])
            .with_exec(['sh', '-c', 'echo gunicorn config ok'])
            .stdout()
        )
# No heading:4 ends here
