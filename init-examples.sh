#!/usr/bin/env bash
# [[file:TECHNICAL.org::*init-examples.sh][init-examples.sh:1]]
set -eu
cd "$(dirname "$0")"
args=""
if [ "${1:-}" = "--from-scratch" ]; then
    args="--from-scratch"
    shift
elif [ "${1:-}" = "--no-cache" ]; then
    args="--no-cache"
    shift
fi
exec dagger ${DAGGER_EXTRA_ARGS:-} call dind-init-examples $args -o .
# init-examples.sh:1 ends here
