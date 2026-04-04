;; [[file:TECHNICAL.org::*Editor configuration][Editor configuration:1]]
((org-mode
  . ((org-babel-default-header-args:python
      . ((:preserve-indentation . t)))
     (org-id-link-to-org-use-id . nil)
     (eval . (load (expand-file-name "check-result.el"
                     (locate-dominating-file default-directory ".dir-locals.el"))
                   t)))))
;; Editor configuration:1 ends here
