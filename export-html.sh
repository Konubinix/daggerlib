#!/usr/bin/env bash
# [[file:TECHNICAL.org::*export-html.sh][export-html.sh:1]]
set -eu
cd "$(dirname "$0")"
exec dagger ${DAGGER_EXTRA_ARGS:-} call export-html export --path _site
# export-html.sh:1 ends here
