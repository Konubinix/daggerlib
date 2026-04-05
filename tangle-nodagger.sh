#!/usr/bin/env bash
# [[file:TECHNICAL.org::*Tangle without dagger (bootstrap)][Tangle without dagger (bootstrap):1]]
# Bootstrap tangle using host tools (emacs, git, ruff).
# Usage:
#   ./tangle-nodagger.sh                 # tangle only mode 2 bootstrap files
#   ./tangle-nodagger.sh src/foo.org     # tangle a specific file
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Pin org-mode version for reproducible tangle output
ORG_PIN="1025e3b49a98f175b124dbccd774918360fe7e11"
ORG_DIR="$SCRIPT_DIR/.tangle-deps/org"
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
    local tangled_list
    tangled_list=$(emacs --batch --no-init-file \
        -l "$SCRIPT_DIR/tangle.el" \
        --eval "(progn
                  (require 'org)
                  (find-file \"$orgfile\")
                  (let ((files (org-babel-tangle)))
                    (dolist (f files) (princ (format \"%s\n\" f))))
                  (kill-buffer))" 2>&1 | grep -E '^/' || true)
    # Post-process tangled files
    for f in $tangled_list; do
        [ -f "$f" ] || continue
        # Strip trailing whitespace
        sed -i 's/[[:space:]]*$//' "$f"
        # Format Python files
        case "$f" in
            *.py) ruff format --quiet "$f" 2>/dev/null || true ;;
        esac
    done
}

if [ $# -eq 0 ]; then
    # Bootstrap only: tangle the files that produce mode 2 infrastructure
    for f in "$SCRIPT_DIR"/TECHNICAL.org "$SCRIPT_DIR"/src/dev.org "$SCRIPT_DIR"/tests/testing.org; do
        [ -f "$f" ] && tangle_file "$f"
    done
else
    for f in "$@"; do
        tangle_file "$(realpath "$f")"
    done
fi
# Tangle without dagger (bootstrap):1 ends here
