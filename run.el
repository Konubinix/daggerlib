;; [[file:TECHNICAL.org::*Run configuration][Run configuration:1]]
;;; run.el --- Batch-execute org-babel bash blocks -*- lexical-binding: t; -*-

(defun dagger-run-file (orgfile)
  "Execute all named bash blocks in ORGFILE and save the results."
  (find-file orgfile)
  (let ((org-babel-sh-command "bash --norc"))
    (org-babel-map-src-blocks nil
      (let ((name (org-element-property :name (org-element-at-point))))
        (when (and (string= lang "bash") name)
          (message "%s Executing %s..." (format-time-string "%H:%M:%S") name)
          (org-babel-execute-src-block)))))
  (save-buffer)
  (kill-buffer))

;;; run.el ends here
;; Run configuration:1 ends here
