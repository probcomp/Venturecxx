;;;###autoload
(define-derived-mode venture-mode scheme-mode "Venture"
  "Major mode for editing Venture code.
Editing commands are similar to those of `lisp-mode'.

Commands:
Delete converts tabs to spaces as it moves back.
Blank lines separate paragraphs.  Semicolons start comments.
\\{scheme-mode-map}
Entering this mode runs the hooks `scheme-mode-hook' and then
`venture-mode-hook'."
  (setq font-lock-defaults '(venture-font-lock-keywords
			     nil t (("_" . "w"))
			     beginning-of-defun
			     (font-lock-mark-block-function . mark-defun)))
  (set (make-local-variable 'imenu-case-fold-search) nil)
  (setq imenu-generic-expression dsssl-imenu-generic-expression)
  (set (make-local-variable 'imenu-syntax-alist)
       '(("_" . "w"))))

(defvar venture-font-lock-keywords '() 
  "Default expressions to highlight in Venture mode.")
(setq venture-font-lock-keywords
  (eval-when-compile
    (list
     (list "[([]\\(define\\)\\>[ \t]*\\(\\sw+\\)\\>"
           '(1 font-lock-keyword-face)
           '(2 font-lock-function-name-face))
     (list "[([]\\(assume\\)\\>[ \t]*\\(\\sw+\\)\\>"
           '(1 font-lock-variable-name-face)
           '(2 font-lock-function-name-face))
     (cons
      (concat
       "(" (regexp-opt
            '(;; Model special forms
              "if" "lambda" "let" "and" "or"
              ;; Inference special forms
              "loop" "do" "begin"
              ;; Not bothering
              ;;"quasiquote" "quote" "unquote"
              "map") t)
       "\\>")
      1)
     (list (concat "\\<" (regexp-opt '("default" "all" "one" "none" "ordered") t) "\\>")
           '(1 font-lock-builtin-face))
     (list (concat "[([]" (regexp-opt '("observe" "predict" "infer" "sample" "collect") t) "\\>")
           '(1 font-lock-variable-name-face))
     )))

;; Candidate faces to use for things: font-lock-builtin-face,
;; font-lock-comment-delimiter-face, font-lock-comment-face
;; font-lock-constant-face font-lock-doc-face
;; font-lock-function-name-face font-lock-keyword-face
;; font-lock-negation-char-face font-lock-preprocessor-face
;; font-lock-string-face font-lock-type-face
;; font-lock-variable-name-face

;; Candidate special forms to highlight:
;; call_back force sample_all forget freeze report? load

;; TODO: I want to set apart the things that put you in the modeling
;; language rather than the inference language (assume, observe,
;; predict, infer).  Is font-lock-variable-name-face good for that?

(provide 'venture-mode)

;; Make Emacs open .vnt files in venture-mode
;;;###autoload
(add-to-list 'auto-mode-alist '("\\.vnt\\'" . venture-mode))
