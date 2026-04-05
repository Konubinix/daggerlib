#!/usr/bin/env bash
# [[file:TECHNICAL.org::*Run without dagger][Run without dagger:1]]
# Execute org-babel blocks and save results.
# Usage:
#   ./run-nodagger.sh                    # run all src and doc org files
#   ./run-nodagger.sh src/foo.org        # run a specific file
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

run_file() {
    local orgfile="$1"
    echo "Running $orgfile..."
    emacs --batch --no-init-file \
        -l "$SCRIPT_DIR/tangle.el" \
        -l "$SCRIPT_DIR/run.el" \
        --eval "(dagger-run-file \"$orgfile\")" 2>&1 || true
}

if [ $# -eq 0 ]; then
    for f in "$SCRIPT_DIR"/src/*.org "$SCRIPT_DIR"/doc/*.org; do
        [ -f "$f" ] && run_file "$f"
    done
else
    for f in "$@"; do
        run_file "$(realpath "$f")"
    done
fi
# Run without dagger:1 ends here
