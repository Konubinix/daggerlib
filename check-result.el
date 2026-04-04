;; [[file:TECHNICAL.org::*Check-result noweb macro][Check-result noweb macro:1]]
;;; check-result.el --- Noweb macros for test scripts

(unless (fboundp 'first) (defalias 'first #'car))
(unless (fboundp 'second) (defalias 'second #'cadr))

(defun dagger-tangle--get-cached-result (name)
  "Extract the #+RESULTS content for block NAME from the current org buffer.
Handles both `: value` and `#+begin_example...#+end_example` formats."
  (save-match-data
  (save-excursion
    (goto-char (point-min))
    (when (re-search-forward
           (format "^[ \t]*#\\+RESULTS\\[.*\\]:[ \t]+%s[ \t]*$" (regexp-quote name))
           nil t)
      (forward-line 1)
      (let ((start (point))
            (lines nil))
        (cond
         ;; #+begin_example block — include trailing newline to match org-babel behavior
         ((looking-at "^[ \t]*#\\+begin_example")
          (forward-line 1)
          (while (not (looking-at "^[ \t]*#\\+end_example"))
            (let ((line (buffer-substring-no-properties
                         (line-beginning-position) (line-end-position))))
              (push line lines))
            (forward-line 1))
          (concat (mapconcat #'identity (nreverse lines) "\n") "\n"))
         ;; : prefixed results
         (t
          (while (looking-at "^[ \t]*: \\(.*\\)$\\|^[ \t]*:$")
            (let ((line (or (match-string 1) "")))
              (push line lines))
            (forward-line 1))
          (mapconcat #'identity (nreverse lines) "\n"))))))))

(defun dagger-tangle--all-check-results ()
  "Return check-result lines for all named bash blocks (except init)."
  (let (names)
    (save-excursion
      (goto-char (point-min))
      (while (re-search-forward
              "^[ \t]*#\\+NAME:[ \t]+\\([a-zA-Z0-9_-]+\\)[ \t]*\n[ \t]*#\\+begin_src bash"
              nil t)
        (let ((name (match-string 1)))
          (unless (string= name "init")
            (push name names)))))
    (mapconcat (lambda (n) (format "check-result(%s)" n))
               (nreverse names) "\n")))

(defun konix/org-babel-expand-noweb-references/add-check-result (orig-func info &optional parent-buffer context)
  (let* ((code (second info))
         (src-buf (or parent-buffer (current-buffer))))
    ;; Expand check-all into check-result(name) for every named bash block
    (setq code (replace-regexp-in-string
                "^[ \t]*check-all[ \t]*$"
                (lambda (_) (save-match-data
                              (with-current-buffer src-buf
                                (dagger-tangle--all-check-results))))
                code nil t))
    ;; Expand each check-result(name) into shell test functions
    (setq code
          (replace-regexp-in-string
           "^[ \t]*check-result(\\([a-zA-Z0-9_-]+\\))"
           (lambda (match)
             (let* ((name (match-string 1 match))
                    (result (save-match-data
                              (with-current-buffer src-buf
                                (dagger-tangle--get-cached-result name)))))
               (concat
                "\n" name "_code () {\n"
                "      <<" name ">>\n"
                "}\n"
                "\n" name "_expected () {\n"
                "      cat<<\"EOEXPECTED\"\n"
                (or result "") "\n"
                "EOEXPECTED\n"
                "}\n"
                "\necho 'Run " name "'\n"
                "\n{ " name "_code || true ; } > \"${TMP}/code.txt\" 2>/dev/null\n"
                name "_expected > \"${TMP}/expected.txt\"\n"
                "diff -uBw \"${TMP}/code.txt\" \"${TMP}/expected.txt\" || {\n"
                "echo \"Something went wrong when trying " name "\"\n"
                "exit 1\n"
                "}\n")))
           code nil t))
    (funcall
     orig-func
     ;; info with the code replaced
     (cons (first info) (cons code (cddr info)))
     parent-buffer)))
(advice-add 'org-babel-expand-noweb-references :around 'konix/org-babel-expand-noweb-references/add-check-result)

;;; check-result.el ends here
;; Check-result noweb macro:1 ends here
