#!/usr/bin/env bash
# [[file:tests/testing.org::*Test without dagger][Test without dagger:1]]
set -eu
cd "$(dirname "$0")"
exec pytest tests/test_use_cases.py -v
# Test without dagger:1 ends here
