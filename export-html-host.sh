#!/usr/bin/env bash
# [[file:TECHNICAL.org::*Export HTML (host)][Export HTML (host):1]]
# Export org files to HTML for GitHub Pages.
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

SITE_DIR="$SCRIPT_DIR/_site"
rm -rf "$SITE_DIR"
mkdir -p "$SITE_DIR"

export_file() {
    local orgfile="$1"
    local relpath
    relpath="$(realpath --relative-to="$SCRIPT_DIR" "$orgfile")"
    local outdir="$SITE_DIR/$(dirname "$relpath")"
    mkdir -p "$outdir"
    echo "Exporting $relpath..."
    local rc=0
    emacs --batch --no-init-file \
        -l "$SCRIPT_DIR/tangle.el" \
        --eval "(progn
                  (require 'ox-html)
                  (find-file \"$orgfile\")
                  ;; Rewrite file: links from .org to .html
                  (setq org-html-link-org-files-as-html t)
                  (org-html-export-to-html)
                  (kill-buffer))" 2>&1 || rc=$?
    if [ "$rc" -ne 0 ]; then
        echo "ERROR: export failed for $relpath (exit $rc)" >&2
        return "$rc"
    fi
    local htmlfile="${orgfile%.org}.html"
    if [ -f "$htmlfile" ]; then
        mv "$htmlfile" "$outdir/"
    fi
}

for f in "$SCRIPT_DIR"/readme.org "$SCRIPT_DIR"/TECHNICAL.org \
         "$SCRIPT_DIR"/src/*.org "$SCRIPT_DIR"/tests/*.org \
         "$SCRIPT_DIR"/examples/*/readme.org; do
    [ -f "$f" ] && export_file "$f"
done

# Root readme becomes index.html
if [ -f "$SITE_DIR/readme.html" ]; then
    cp "$SITE_DIR/readme.html" "$SITE_DIR/index.html"
fi
# Export HTML (host):1 ends here
