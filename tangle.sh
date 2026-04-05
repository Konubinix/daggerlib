#!/usr/bin/env bash
# [[file:TECHNICAL.org::*Tangle script (mode 2)][Tangle script (mode 2):1]]
set -eu
cd "$(dirname "$0")"
exec dagger call dev tangle export --path=.
# Tangle script (mode 2):1 ends here
