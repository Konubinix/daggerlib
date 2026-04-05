#!/usr/bin/env bash
# [[file:TECHNICAL.org::*Run script (mode 2)][Run script (mode 2):1]]
set -eu
cd "$(dirname "$0")"
exec dagger call dev run export --path=.
# Run script (mode 2):1 ends here
