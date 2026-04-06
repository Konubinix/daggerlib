;; [[file:TECHNICAL.org::*Run configuration][Run configuration:1]]
;;; run.el --- Batch-execute org-babel fixtureyaml blocks -*- lexical-binding: t; -*-

(defun dagger-run-file (orgfile)
  "Execute all named fixtureyaml blocks in ORGFILE and save the results."
  (find-file orgfile)
  (org-babel-map-src-blocks nil
    (let ((name (org-element-property :name (org-element-at-point))))
      (when (and name (string= lang "fixtureyaml"))
        (message "%s Executing %s..." (format-time-string "%H:%M:%S") name)
        (org-babel-execute-src-block))))
  (save-buffer)
  (kill-buffer))

;;; run.el ends here
;; Run configuration:1 ends here
