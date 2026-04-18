# [[file:readme.org::+begin_src python :tangle collector.py][No heading:1]]
"""Scan a directory for .log files and print a JSON summary."""
import json
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
summary = [
    {"file": p.name, "lines": len(p.read_text().splitlines())}
    for p in sorted(log_dir.glob("*.log"))
]
print(json.dumps(summary))
# No heading:1 ends here
