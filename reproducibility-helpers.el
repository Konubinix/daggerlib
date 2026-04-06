;; [[file:TECHNICAL.org::*Reproducibility helpers][Reproducibility helpers:1]]
;;; reproducibility-helpers.el --- Post-tangle hooks and fixtureyaml language

(defun daggerlib-ruff-format-after-tangle ()
  "Run ruff format on the current buffer if it is a Python file."
  (when (string-match-p "\\.py\\'" (buffer-file-name))
    (shell-command (format "ruff format --quiet '%s'" (buffer-file-name)))
    (revert-buffer t t t)))

(add-hook 'org-babel-post-tangle-hook #'daggerlib-ruff-format-after-tangle :append)

(defun fixtureyaml--spec-to-cli (yaml-body root)
  "Convert YAML spec body to a dagger call CLI string via generate_tests.py."
  (let ((script (expand-file-name "tests/generate_tests.py" root)))
    (string-trim
     (shell-command-to-string
      (format "echo %s | python3 %s"
              (shell-quote-argument yaml-body)
              (shell-quote-argument script))))))

(defun fixtureyaml--execute-cli (cli root)
  "Execute a CLI command in ROOT directory, return stdout.
Sets up TMP and ROOT environment variables for export/post commands.
Stderr is captured and shown in case of error."
  (let* ((stderr-file (make-temp-file "fixtureyaml-stderr"))
         (tmp-dir (make-temp-file "fixtureyaml-tmp" t))
         (env-setup (format "export TMP=%s ROOT=%s PATH=%s/tests:$PATH"
                            (shell-quote-argument tmp-dir)
                            (shell-quote-argument root)
                            (shell-quote-argument root))))
    (unwind-protect
        (let ((result (string-trim
                       (shell-command-to-string
                        (format "cd %s && %s && { %s ; } 2>%s"
                                (shell-quote-argument root)
                                env-setup
                                cli
                                (shell-quote-argument stderr-file))))))
          (when (and (string-empty-p result)
                     (file-exists-p stderr-file))
            (let ((stderr (string-trim
                           (with-temp-buffer
                             (insert-file-contents stderr-file)
                             (buffer-string)))))
              (unless (string-empty-p stderr)
                (message "fixtureyaml stderr: %s" stderr))))
          result)
      (delete-file stderr-file)
      (delete-directory tmp-dir t))))

(defun fixtureyaml--write-fixture (name yaml-body result root)
  "Write spec and expected files for NAME under ROOT/tests/."
  (let ((specs-dir (expand-file-name "tests/specs/" root))
        (expected-dir (expand-file-name "tests/expected/" root)))
    (make-directory specs-dir t)
    (make-directory expected-dir t)
    (let ((spec-file (expand-file-name (concat name ".yml") specs-dir))
          (expected-file (expand-file-name name expected-dir)))
      (with-temp-file spec-file (insert yaml-body))
      (with-temp-file expected-file (insert result)))))

(defun daggerlib--sha1-hash-strip-dir (orig-fn &optional info context)
  "Advice to strip :dir from params before hashing.
This makes the cache hash independent of the project's absolute path,
so hashes computed in a container match those on the host."
  (let* ((info (or info (org-babel-get-src-block-info)))
         (params (nth 2 info))
         (stripped (cl-remove-if (lambda (p) (eq (car p) :dir)) params))
         (patched (copy-sequence info)))
    (setf (nth 2 patched) stripped)
    (funcall orig-fn patched context)))

(advice-add 'org-babel-sha1-hash :around #'daggerlib--sha1-hash-strip-dir)

(defun fixtureyaml--bash-cache-hash (cli)
  "Compute the org-babel cache hash for a bash block with body CLI.
Uses a temp buffer that inherits the current org file's properties."
  (let ((src-buffer (current-buffer))
        (block-text (concat "#+begin_src bash :exports code :eval no-export\n"
                            cli "\n"
                            "#+end_src\n")))
    (with-temp-buffer
      (org-mode)
      (let ((props (with-current-buffer src-buffer
                     (save-excursion
                       (goto-char (point-min))
                       (let (lines)
                         (while (re-search-forward
                                 "^#\\+PROPERTY:.*" nil t)
                           (push (match-string 0) lines))
                         (mapconcat #'identity (nreverse lines) "\n"))))))
        (insert props "\n\n" block-text))
      (org-set-regexps-and-options)
      (goto-char (point-max))
      (re-search-backward "#\\+begin_src bash")
      (org-babel-sha1-hash (org-babel-get-src-block-info)))))

(defun fixtureyaml--format-output (cli result)
  "Format CLI and RESULT as org markup: a bash src block with cached result."
  (let ((hash (fixtureyaml--bash-cache-hash cli)))
    (concat "#+begin_src bash :exports code :eval no-export\n"
            cli "\n"
            "#+end_src\n"
            "\n"
            "#+RESULTS[" hash "]:\n"
            (mapconcat (lambda (line) (concat ": " line))
                       (split-string result "\n")
                       "\n"))))

(defun org-babel-execute:fixtureyaml (body params)
  "Execute a fixtureyaml block: generate CLI, run it, write fixtures.
Returns org markup (bash block + result) for display in a :results drawer."
  (let* ((info (org-babel-get-src-block-info t))
         (name (nth 4 info))
         (root (expand-file-name
                (locate-dominating-file default-directory "dagger.json")))
         (cli (fixtureyaml--spec-to-cli body root))
         (result (fixtureyaml--execute-cli cli root)))
    (when name
      (fixtureyaml--write-fixture name body result root))
    (fixtureyaml--format-output cli result)))

;; :cache yes skips execution when the block hasn't changed.
;; :results drawer wraps the output so org can replace it cleanly.
;; :exports results shows only the CLI + result on export, hiding the YAML.
(setq org-babel-default-header-args:fixtureyaml
      '((:cache . "yes")
        (:results . "drawer")
        (:exports . "results")))

;;; reproducibility-helpers.el ends here
;; Reproducibility helpers:1 ends here
