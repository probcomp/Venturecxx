(declare (usual-integrations))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

(define-structure (evaluation-context
                   (safe-accessors #t)
                   (conc-name evc-))
  exp
  env
  addr
  trace
  read-traces)

(define-structure address) ; Opaque

(define-structure (rdb (safe-accessors #t))
  )

;; A standard lexical environment structure; holds addresses into
;; traces rather than values.
(define-structure (env-frame (safe-accessors #t))
  parent
  symbols
  addresses) ; Parallel lists mapping symbols to addresses

;; Compound procedures
(define-structure (compound (safe-accessors #t))
  formals
  body
  env
  trace
  read-traces)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (eval exp env trace addr read-traces)
  (trace-search-one trace addr (lambda (v) v)
   (lambda ()
     (let ((answer (do-eval exp env trace addr read-traces)))
       ;; And maybe metadata depending on what kind of trace it is.
       ;; The metadata is presumably dependent on the structure of
       ;; the thunk, so this abstraction will not endure
       (record! trace exp env addr read-traces answer)
       answer))))

(define (do-eval exp env trace addr read-traces)
  (case* exp
    ((constant val) val)
    ((var x)
     (env-search env x
      (lambda (addr)
        (traces-lookup (cons trace read-traces) addr))
      (lambda ()
        ((access eval system-global-environment) x user-initial-environment))))
    ((lambda-form formals body)
     ;; Do I need to close over the maker address?
     (make-compound formals body env trace read-traces))
    ;; Interesting new operation: evaluate in a subtrace.  Adding a
    ;; new trace frame like this hides the nested evaluation from
    ;; appearing in the current trace, and can shield the current
    ;; trace from reflective changes made to the nexted one if the
    ;; trace modification policy enforces that.
    ((extend-form subform)
     (let ((subtrace (trace-extend trace))
           (addr* (extend-address addr 'ext)))
       ;; Could add trace to read-traces here instead of stashing
       ;; it in the parent pointer
       (eval subform env subtrace addr* read-traces)))
    ;; Permit reflection on the evaluation context
    ((nullary-magic 'get-current-environment) env)
    ((nullary-magic 'get-current-trace) trace)
    ((nullary-magic 'get-current-read-traces) read-traces)
    ((definition x subexp)
     (let ((addr* (extend-address addr 'defn)))
       (eval subexp env trace addr* read-traces)
       (env-bind! env x addr*)))
    ((if-form p c a)
     (if (eval p env trace (extend-address addr 'if-p) read-traces)
         (eval c env trace (extend-address addr 'if-c) read-traces)
         (eval a env trace (extend-address addr 'if-a) read-traces)))
    ((begin-form forms)
     (let ()
       (define result #f)
       (for-each
        (lambda (s i)
          (let ((addr* (extend-address addr `(begin ,i))))
            (set! result (eval s env trace addr* read-traces))))
        forms
        (iota (length forms)))
       result))
    (else ;; Application
     (let ((subaddrs (map (lambda (e i)
                            (let ((addr* (extend-address addr `(app-sub ,i))))
                              (eval e env trace addr* read-traces)
                              addr*))
                          (subforms exp)
                          (iota (length (subforms exp))))))
       (apply (car subaddrs) (cdr subaddrs) addr trace read-traces)))))

(define (apply oper opands addr cur-trace read-traces)
  (let ((oper (trace-lookup cur-trace oper)))
    (cond ((primitive? oper)
           ((primitive-apply oper) opands))
          ((compound? oper)
           (let ((formals (compound-formals oper))
                 (body (compound-body oper))
                 (env (compound-env oper))
                 (trace (compound-trace oper))
                 (read-traces (compound-read-traces oper)))
             (let ((env* (extend-env env formals opands))
                   (trace* cur-trace)
                   (addr* (extend-address addr 'app))
                   ;; This way, a compound procedure does not carry
                   ;; write permission to the trace in which it was
                   ;; created
                   (read-traces* (cons trace read-traces)))
               (eval body env* trace* addr* read-traces*))))
          ((procedure? oper) ; An MIT Scheme procedure
           (let ((arguments (map (lambda (o)
                                   (traces-lookup (cons cur-trace read-traces) o))
                                 opands)))
             ((access apply system-global-environment) oper arguments))))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (env-search env symbol win lose)
  (if (env-frame? env)
      (let loop ((ss (env-frame-symbols env))
                 (as (env-frame-addresses env)))
        (cond ((null? ss)
               (env-search (env-frame-parent env) symbol win lose))
              ((eq? (car ss) symbol)
               (win (car as)))
              (else (loop (cdr ss) (cdr as)))))
      (lose)))
(define extend-env make-env-frame)
(define (env-bind! env sym addr)
  (set-env-frame-symbols! env (cons sym (env-frame-symbols env)))
  (set-env-frame-addresses! env (cons addr (env-frame-addresses env))))
