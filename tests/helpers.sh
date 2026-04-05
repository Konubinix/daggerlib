#!/usr/bin/env bash
# [[file:testing.org::*Test sandbox setup][Test sandbox setup:1]]
unset HISTFILE
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
export ROOT=$(while [ ! -f dagger.json ]; do cd ..; done && pwd)
export PATH="${ROOT}/tests:$PATH"
# Test sandbox setup:1 ends here
