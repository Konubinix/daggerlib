;; [[file:TECHNICAL.org::*Tangle configuration][Tangle configuration:1]]
;;; tangle.el --- Self-contained org-babel tangling for dagger lib -*- lexical-binding: t; -*-

;; Don't prompt for code block evaluation
(setq org-confirm-babel-evaluate nil)

;; In batch mode, any interactive prompt means something is misconfigured
;; (e.g. unknown language with :comments yes).  Fail loudly instead of
;; hanging or silently skipping blocks.
(when noninteractive
  (dolist (fn '(read-string read-from-minibuffer completing-read))
    (advice-add fn :before
                (lambda (&rest _)
                  (error "Tangle aborted: batch Emacs cannot interact (check language modes in tangle.el)")))))

;; Load pinned org-mode from .tangle-deps BEFORE anything else loads the
;; built-in org.  This must happen before (require 'ob-shell) since that
;; transitively loads org.
(let ((org-lisp-dir
       (expand-file-name ".tangle-deps/org/lisp"
                         (file-name-directory (or load-file-name buffer-file-name)))))
  (when (file-directory-p org-lisp-dir)
    (push org-lisp-dir load-path)
    (let ((contrib (expand-file-name "../contrib/lisp" org-lisp-dir)))
      (when (file-directory-p contrib)
        (push contrib load-path)))
    ;; Force load of pinned org (unload built-in if already loaded)
    (require 'org)))

;; Load babel languages needed for tangling
(require 'ob-shell)
(require 'ob-python)

;; Map nix to conf-mode so #+begin_src nix blocks tangle without nix-mode
(add-to-list 'org-src-lang-modes '("nix" . conf))

;; Add link comments and blank lines between blocks in tangled output
(setq org-babel-default-header-args
      (cons '(:comments . "yes")
            (cons '(:padline . "yes")
                  (assq-delete-all :comments
                    (assq-delete-all :padline
                      org-babel-default-header-args)))))

;; Preserve indentation in Python blocks so that org-level indentation
;; does not interfere with Python's significant whitespace.
(add-to-list 'org-babel-default-header-args:python
             '(:preserve-indentation . t))

;; Load reproducibility helpers (shared with interactive Emacs
;; via .dir-locals.el).
(load (expand-file-name "reproducibility-helpers.el"
         (file-name-directory (or load-file-name buffer-file-name)))
      t)

;; After tangling, auto-generate tests/expected/ files from #+RESULTS
;; for every block that tangled to tests/commands/.
(advice-add 'org-babel-tangle :filter-return
            (lambda (files)
              (daggerlib--write-expected-files files)
              files))

;; Strip trailing whitespace in the per-block tangle buffer.  Doing this
;; inside the body-hook (instead of `sed -i' post-emacs) keeps the tangle
;; buffer byte-identical to the on-disk file, so org-babel-tangle's
;; compare-buffer-substrings (ob-tangle.el:320) skips write-region — no
;; mtime change, Dagger's Directory.diff stays empty, downstream caches
;; (notably ./test.sh) survive across runs.
(add-hook 'org-babel-tangle-body-hook #'delete-trailing-whitespace)

;;; tangle.el ends here
;; Tangle configuration:1 ends here
