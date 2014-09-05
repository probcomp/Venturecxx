(declare (usual-integrations))

(define ((tagged-list? tag) thing)
  (and (pair? thing)
       (eq? (car thing) tag)))

(define (constant? exp)
  (and (not (symbol? exp))
       (or (not (pair? exp))
           (eq? (car exp) 'quote))))
(define (constant-value exp)
  (if (pair? exp)
      (cadr exp)
      exp))
(define-algebraic-matcher constant constant? constant-value)

(define begin-form? (tagged-list? 'begin))
;; Wins with list of expressions
(define-algebraic-matcher begin-form begin-form? cdr)

(define definition? (tagged-list? 'define))
;; Wins with variable and expression
(define-algebraic-matcher definition definition? cadr caddr)

(define (var? thing) (symbol? thing))
(define-algebraic-matcher var var? id-project)

(define if-form? (tagged-list? 'if))
(define-algebraic-matcher if-form if-form? cadr caddr cadddr)

(define lambda-form? (tagged-list? 'lambda))
(define-algebraic-matcher lambda-form lambda-form? cadr caddr)

(define trace-in-form? (tagged-list? 'trace-in))
(define-algebraic-matcher trace-in-form trace-in-form? cadr caddr)

(define extend-form? (tagged-list? 'ext))
(define-algebraic-matcher extend-form extend-form? cadr)

;;; Special forms Kernel-style
(define-structure (operative (safe-accessors #t)) procedure)
(define operatives '())
(define (register-operative! name operative)
  (set! operatives (cons (cons name operative) operatives)))

(define-syntax define-operative
  (syntax-rules ()
    ((_ (name arg ...) body ...)
     (register-operative! 'name (make-operative (lambda (arg ...) body ...))))))

;; Permit reflection on the evaluation context
(define-operative (get-current-environment subforms env addr trace read-traces) env)
(define-operative (get-current-trace subforms env addr trace read-traces) trace)
(define-operative (get-current-read-traces subforms env addr trace read-traces) read-traces)

(define-integrable (operative-form form win lose)
  (if (pair? form)
      (aif (assq (car form) operatives)
           (win (cdr it) (cdr form))
           (lose))
      (lose)))
