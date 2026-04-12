;; [[file:TECHNICAL.org::*Run configuration][Run configuration:1]]
;;; run.el --- Batch-execute org-babel bash blocks -*- lexical-binding: t; -*-

    (defun dagger-run-file (orgfile &optional no-cache)
      "Execute bash blocks in ORGFILE.
When NO-CACHE is non-nil, ignore cached results."
      (find-file orgfile)
      (org-babel-map-src-blocks nil
        (when (and (string= lang "bash")
                   (not (assq :init (nth 2 (org-babel-get-src-block-info t)))))
          (message "%s Executing %s %s..." (format-time-string "%H:%M:%S") lang
                   (or (org-element-property :name (org-element-at-point)) "(unnamed)"))
          (if no-cache
              (org-babel-execute-src-block nil nil '((:cache . "no")))
            (org-babel-execute-src-block))))
      (save-buffer)
      (kill-buffer))

    (defvar dagger--block-error nil)

    (defun dagger--capture-error (exit-code stderr)
      "Advice: capture block failure details (ignore stderr-only warnings)."
      (when (and (numberp exit-code) (> exit-code 0))
        (setq dagger--block-error
              (format "exit %s:\n%s" exit-code (or stderr "")))))

    (defun dagger--execute-or-die (&optional info params)
      "Execute src block; signal error if it exits non-zero."
      (setq dagger--block-error nil)
      (advice-add 'org-babel-eval-error-notify :before #'dagger--capture-error)
      (unwind-protect
          (if (and info params)
              (org-babel-execute-src-block nil info params)
            (org-babel-execute-src-block))
        (advice-remove 'org-babel-eval-error-notify #'dagger--capture-error))
      (when dagger--block-error
        (error "Block failed (%s)" dagger--block-error)))

    (defun dagger-init-file (orgfile &optional no-cache)
      "Execute init bash blocks (those with :init yes) in ORGFILE.
When NO-CACHE is non-nil, ignore cached results.
Stops at first failure."
      (find-file orgfile)
      (org-babel-map-src-blocks nil
        (let* ((info (org-babel-get-src-block-info t))
               (params (nth 2 info)))
          (when (and (string= lang "bash")
                     (assq :init params))
            (message "%s Init %s..." (format-time-string "%H:%M:%S")
                     (or (org-element-property :name (org-element-at-point)) "(unnamed)"))
            (if no-cache
                (dagger--execute-or-die info '((:cache . "no")))
              (dagger--execute-or-die)))))
      (save-buffer)
      (kill-buffer))

    ;;; run.el ends here
;; Run configuration:1 ends here
