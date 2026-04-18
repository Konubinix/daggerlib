# [[file:readme.org::+begin_src python :tangle service.py][No heading:3]]
"""Minimal service that logs a startup message with timezone info."""
from datetime import datetime

tz = datetime.now().astimezone().tzname()
print(f"service started (timezone: {tz})")
# No heading:3 ends here
