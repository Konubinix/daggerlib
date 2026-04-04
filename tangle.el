;; [[file:TECHNICAL.org::*Tangle configuration][Tangle configuration:1]]
;;; tangle.el --- Self-contained org-babel tangling for dagger lib -*- lexical-binding: t; -*-

;; Don't prompt for code block evaluation
(setq org-confirm-babel-evaluate nil)

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

;; Load check-result noweb macro support (shared with interactive Emacs
;; via .dir-locals.el).
(load (expand-file-name "check-result.el"
         (file-name-directory (or load-file-name buffer-file-name)))
      t)

;;; tangle.el ends here
;; Tangle configuration:1 ends here
