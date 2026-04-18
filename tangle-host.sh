#!/usr/bin/env bash
# [[file:TECHNICAL.org::*Tangle script (host)][Tangle script (host):1]]
# Tangle all org files.
# Usage:
#   ./tangle.sh                          # tangle all org files
#   ./tangle.sh src/foo.org              # tangle a specific file
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure pinned org-mode is cloned and up-to-date
ORG_PIN="1025e3b49a98f175b124dbccd774918360fe7e11"
ORG_DIR="$SCRIPT_DIR/.tangle-deps/org"
if [ -d "$ORG_DIR" ] && [ "$(git -C "$ORG_DIR" rev-parse HEAD 2>/dev/null)" != "$ORG_PIN" ]; then
    echo "Org-mode pin changed, re-cloning..."
    rm -rf "$ORG_DIR"
fi
if [ ! -d "$ORG_DIR" ]; then
    echo "Cloning pinned org-mode ($ORG_PIN)..."
    mkdir -p "$SCRIPT_DIR/.tangle-deps"
    git clone --quiet https://git.savannah.gnu.org/git/emacs/org-mode.git "$ORG_DIR"
    git -C "$ORG_DIR" checkout --quiet "$ORG_PIN"
    # Generate org-loaddefs.el and org-version.el (needed for org to load properly)
    emacs --batch --no-init-file \
        --eval "(progn
                  (push \"$ORG_DIR/lisp\" load-path)
                  (require 'autoload)
                  (setq generated-autoload-file \"$ORG_DIR/lisp/org-loaddefs.el\")
                  (update-directory-autoloads \"$ORG_DIR/lisp\"))" 2>/dev/null
    ORG_GIT_VERSION=$(git -C "$ORG_DIR" describe --tags --match "release_*" 2>/dev/null || echo "N/A")
    ORG_RELEASE=$(echo "$ORG_GIT_VERSION" | sed 's/^release_//;s/-.*//')
    (cd "$ORG_DIR/lisp" && emacs --batch --no-init-file \
        --eval "(progn
                  (push \"$ORG_DIR/lisp\" load-path)
                  (load \"$ORG_DIR/mk/org-fixup.el\")
                  (org-make-org-version \"$ORG_RELEASE\"
                                        \"$ORG_GIT_VERSION\"))") 2>/dev/null || true
fi

tangle_file() {
    local orgfile="$1"
    echo "Tangling $orgfile..."
    local raw_output rc=0
    raw_output=$(emacs --batch --no-init-file \
        -l "$SCRIPT_DIR/tangle.el" \
        --eval "(progn
                  (require 'org)
                  (find-file \"$orgfile\")
                  (let ((files (org-babel-tangle)))
                    (dolist (f files) (princ (format \"%s\n\" f))))
                  (kill-buffer))" 2>&1) || rc=$?
    if [ "$rc" -ne 0 ]; then
        echo "ERROR: emacs tangle failed (exit $rc):" >&2
        echo "$raw_output" >&2
        return "$rc"
    fi
}

if [ $# -eq 0 ]; then
    for f in "$SCRIPT_DIR"/readme.org "$SCRIPT_DIR"/TECHNICAL.org \
             "$SCRIPT_DIR"/src/*.org "$SCRIPT_DIR"/tests/*.org \
             "$SCRIPT_DIR"/examples/*/readme.org; do
        [ -f "$f" ] && tangle_file "$f"
    done
else
    for f in "$@"; do
        tangle_file "$(realpath "$f")"
    done
fi
# Tangle script (host):1 ends here
