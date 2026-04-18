;; [[file:TECHNICAL.org::*Reproducibility helpers][Reproducibility helpers:1]]
;;; reproducibility-helpers.el --- Tangle helpers for test commands

  (defun daggerlib--test-base-dir ()
    "Return the base directory for test files.
  For example org files (under examples/) use the example directory.
  For library org files (under src/) use the project root."
    (let* ((root (locate-dominating-file default-directory "dagger.json"))
           (rel (file-relative-name default-directory root)))
      (if (string-prefix-p "examples/" rel)
          default-directory
        root)))

  (defun daggerlib-auto-test ()
    "Derive tangle path for test command from the block's #+NAME."
    (let ((name (org-element-property :name (org-element-at-point))))
      (unless name (error "daggerlib-auto-test: no #+NAME on this block"))
      (expand-file-name (concat "tests/commands/" name)
                        (daggerlib--test-base-dir))))

  (defun daggerlib--extract-result (name)
    "Extract cached #+RESULTS lines for NAME in current buffer."
    (save-excursion
      (goto-char (point-min))
      (when (re-search-forward
             (format "^[ \t]*#\\+RESULTS\\(?:\\[.*\\]\\)?:[ \t]+%s"
                     (regexp-quote name))
             nil t)
        (forward-line 1)
        (let ((lines nil))
          (while (looking-at "^[ \t]*: \\(.*\\)")
            (push (match-string-no-properties 1) lines)
            (forward-line 1))
          (when lines
            (mapconcat #'identity (nreverse lines) "\n"))))))

  (defun daggerlib--write-expected-files (tangled-files)
    "For each tangled command file, write expected output from #+RESULTS.
Skip the write when content is already up-to-date — rewriting unchanged files
would bump mtimes and invalidate Dagger's Directory.diff downstream."
    (let ((root (locate-dominating-file default-directory "dagger.json")))
      (dolist (f tangled-files)
        (when (string-match "/tests/commands/\\([^/]+\\)$" f)
          (let* ((name (match-string 1 f))
                 (result (daggerlib--extract-result name)))
            (when result
              (let* ((cmd-rel (file-relative-name f root))
                     (exp-rel (replace-regexp-in-string
                               "/commands/" "/expected/" cmd-rel))
                     (expected-file (expand-file-name exp-rel root))
                     (new-content (concat result "\n"))
                     (old-content (when (file-exists-p expected-file)
                                    (with-temp-buffer
                                      (insert-file-contents-literally
                                       expected-file)
                                      (buffer-string)))))
                (unless (equal new-content old-content)
                  (make-directory (file-name-directory expected-file) t)
                  (with-temp-file expected-file
                    (insert new-content))
                  (message "auto-expected: %s" expected-file)))))))))

  ;;; reproducibility-helpers.el ends here
;; Reproducibility helpers:1 ends here
