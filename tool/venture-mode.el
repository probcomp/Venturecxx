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
  (setq font-lock-defaults '((venture-font-lock-keywords
                              venture-font-lock-keywords-1
                              venture-font-lock-keywords-2
                              venture-font-lock-keywords-3)
                             nil t (("_" . "w"))
                             beginning-of-defun
                             (font-lock-mark-block-function . mark-defun)))
  (set (make-local-variable 'imenu-case-fold-search) nil)
  (setq imenu-generic-expression dsssl-imenu-generic-expression)
  (set (make-local-variable 'imenu-syntax-alist)
       '(("_" . "w"))))

(defvar venture-font-lock-keywords-1 nil)
(setq venture-font-lock-keywords-1
      ;; Declarations, by analogy with scheme-mode
      (eval-when-compile
        (list
         (list "[([]\\(define\\)\\>[ \t]*\\(\\sw+\\)\\>"
               '(1 font-lock-type-face)
               '(2 font-lock-function-name-face))
         (list "[([]\\(assume\\)\\>[ \t]*\\(\\sw+\\)\\>"
               '(1 font-lock-keyword-face)
               '(2 font-lock-function-name-face)))))

(defvar venture-font-lock-keywords-2 nil)
(setq venture-font-lock-keywords-2
      ;; Control structures, special forms, modeling directives
      ;; Some of these (e.g "load") don't fit neatly into a category, so
      ;; I chose something arbitrary but hopefully not unreasonable.
      (append venture-font-lock-keywords-1
              (eval-when-compile
                (list
                 (list (concat "(" (regexp-opt '(;; Model special forms
                                                 "if" "lambda" "let" "and"
                                                 "or" "identity") t)
                               "\\>")
                       '(1 font-lock-keyword-face))
                 (list (concat "(" (regexp-opt '(;; Inference special forms
                                                 "loop" "do" "begin"
                                                 "call_back") t)
                               "\\>")
                       '(1 font-lock-type-face))
                 (list (concat "(" (regexp-opt
                                    '(;; Quoting
                                      "quasiquote" "quote" "unquote") t)
                               "\\>")
                       '(1 font-lock-string-face))
                 (list (concat "\\<" (regexp-opt
                                      '(;; Inference scopes
                                        "default" "all" "one" "none"
                                        "ordered") t) "\\>")
                       '(1 font-lock-builtin-face))
                 (list (concat "[([]" (regexp-opt
                                       '(;; Modeling directives
                                         ;; Load isn't really a directive, but doesn't fit anywhere else
                                         "observe" "predict" "infer"
                                         "sample" "sample_all"
                                         "collect" "force" "forget" "freeze"
                                         "load") t) "\\>")
                       '(1 font-lock-keyword-face))
                 (list (concat "\\<" (regexp-opt
                                      '(;; Inference prelude SP's
                                        "bind" "bind_" "curry" "curry3"
                                        "global_likelihood" "global_posterior"
                                        "iterate" "mapM" "pass" "repeat" "return"
                                        "sequence") t) "\\>")
                       '(1 font-lock-type-face))))))

(defvar venture-font-lock-keywords-3 nil)
(setq venture-font-lock-keywords-3
      ;; These are likely to change over time. To get an updated list,
      ;; call the script venture_mode_font_lock.py in the "tool" directory
      ;; with the appropriate argument.
      ;; Call with no arguments for list of valid arguments to pass.
      ;; Unfortunately, the resulting list will not be perfect. For instance,
      ;; "forget" and "freeze" show up as inference SP's, but are also included
      ;; up above as directives. Fortunately, font-lock-keywords with lower
      ;; numbers take precedence.
      (append venture-font-lock-keywords-2
              (eval-when-compile
                (list
                 (list
                  (concat "\\<" (regexp-opt
                                 '(;; Model SP's. For updated list, call:
                                   ;; "python venture_mode_font_lock.py model_SPs"
                                   "add" "apply" "apply_function" "arange" "array"
                                   "atan2" "atom_eq" "bernoulli" "beta" "binomial"
                                   "biplex" "branch" "categorical" "contains"
                                   "cos" "diag_matrix" "dict" "dirichlet" "div"
                                   "eq" "eval" "exactly" "exp" "expon"
                                   "extend_environment" "first" "flip" "floor"
                                   "gamma" "get_current_environment"
                                   "get_empty_environment" "gt" "gte" "hypot"
                                   "id_matrix" "imapv" "inv_gamma" "inv_wishart"
                                   "is_array" "is_atom" "is_boolean" "is_dict"
                                   "is_environment" "is_integer" "is_matrix"
                                   "is_number" "is_pair" "is_probability"
                                   "is_procedure" "is_simplex" "is_symbol"
                                   "is_vector" "laplace" "linspace" "list" "log"
                                   "log_bernoulli" "log_flip" "lookup" "lt" "lte"
                                   "make_beta_bernoulli" "make_cmvn" "make_crp"
                                   "make_csp" "make_dir_mult" "make_gp"
                                   "make_lazy_hmm" "make_sym_dir_mult"
                                   "make_uc_beta_bernoulli" "make_uc_dir_mult"
                                   "make_uc_sym_dir_mult" "mapv" "matrix"
                                   "matrix_mul" "mem" "min" "mod" "mul"
                                   "multivariate_normal" "normal" "not" "pair"
                                   "poisson" "pow" "print" "probability" "ravel"
                                   "real" "repeat" "rest" "second" "simplex" "sin"
                                   "size" "sqrt" "student_t" "sub"
                                   "symmetric_dirichlet" "tag" "tag_exclude" "tan"
                                   "to_array" "to_list" "to_vector"
                                   "uniform_continuous" "uniform_discrete"
                                   "vector" "vector_dot" "vonmises" "wishart"
                                   "zip") t)
                          "\\>")
                  '(1 font-lock-builtin-face))
                 (list
                  (concat "\\<" (regexp-opt
                                 '(;; Inference SP's. For updated list, call:
                                   ;; "python venture_mode_font_lock.py inference_SPs"
                                   "assert" "bogo_possibilize" "collapse_equal"
                                   "collapse_equal_map" "draw_scaffold" "emap"
                                   "empty" "enumerative_diversify" "func_mh"
                                   "func_pgibbs" "func_pmap" "gibbs"
                                   "gibbs_update" "hmc" "in_model" "incorporate"
                                   "into" "likelihood_at" "likelihood_weight"
                                   "load_plugin" "map" "meanfield" "mh"
                                   "mh_kernel_update" "nesterov" "new_model"
                                   "ordered_range" "particle_log_weights"
                                   "pgibbs" "pgibbs_update" "plotf"
                                   "plotf_to_file" "posterior_at" "print"
                                   "print_scaffold_stats" "printf" "rejection"
                                   "resample" "resample_multiprocess"
                                   "resample_serializing" "resample_thread_ser"
                                   "resample_threaded"
                                   "set_particle_log_weights" "slice"
                                   "slice_doubling" "subsampled_mh"
                                   "subsampled_mh_check_applicability"
                                   "subsampled_mh_make_consistent" "sweep") t)
                          "\\>")
                  '(1 font-lock-builtin-face))))))

(defvar venture-font-lock-keywords nil
  "Default expressions to highlight in Venture")
(setq venture-font-lock-keywords venture-font-lock-keywords-1)

;; Candidate special forms to highlight:
;; report?

(provide 'venture-mode)

;; Make Emacs open .vnt files in venture-mode
;;;###autoload
(add-to-list 'auto-mode-alist '("\\.vnt\\'" . venture-mode))
