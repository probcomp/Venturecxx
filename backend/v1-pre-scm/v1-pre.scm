(declare (usual-integrations))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;; Types

(define-structure (evaluation-context
                   (safe-accessors #t)
                   (conc-name evc-))
  exp
  env
  addr
  trace
  read-traces)

(define-structure address) ; Opaque

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

;; Eventually, primmitive procedures will have optional densities and
;; such, but I don't need any yet.
(define-structure (primitive (safe-accessors #t))
  simulate
  (log-density #f))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;; Essential evaluation

(define (eval exp env trace addr read-traces)
  ;; TODO What happens if this address is recorded, but not in the
  ;; current trace?
  (trace-search trace addr (lambda (v) v)
   (lambda ()
     (let ((answer (do-eval exp env trace addr read-traces)))
       ;; The trace can substitute the return value as well as
       ;; recording
       (record! trace exp env addr read-traces answer)))))

(define (do-eval exp env trace addr read-traces)
  (case* exp
    ((constant val) (scheme->venture val))
    ((var x)
     (env-search env x
      (lambda (addr)
        (traces-lookup (cons trace read-traces) addr))
      (lambda ()
        (scheme->venture
         ((access eval system-global-environment) x user-initial-environment)))))
    ((lambda-form formals body)
     ;; Do I need to close over the maker address?
     (make-compound formals body env trace read-traces))
    ;; Interesting new operation: evaluate in a subtrace.  Adding a
    ;; new trace frame like this hides the nested evaluation from
    ;; appearing in the current trace, and can shield the current
    ;; trace from reflective changes made to the nested one if the
    ;; trace modification policy enforces that.
    ((extend-form subform)
     (let ((subtrace (trace-extend trace))
           (addr* (extend-address addr 'ext)))
       ;; Could add trace to read-traces here instead of stashing
       ;; it in the parent pointer
       (eval subform env subtrace addr* read-traces)))
    ;; Permit reflection on the evaluation context
    (((nullary-magic 'get-current-environment)) env)
    (((nullary-magic 'get-current-trace)) trace)
    (((nullary-magic 'get-current-read-traces)) read-traces)
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
    (_ ;; Application
     (let ((subaddrs (map (lambda (e i)
                            (let ((addr* (extend-address addr `(app-sub ,i))))
                              (eval e env trace addr* read-traces)
                              addr*))
                          exp ; The subforms
                          (iota (length exp)))))
       (apply (car subaddrs) (cdr subaddrs) addr trace read-traces)))))

(define (apply oper opands addr cur-trace read-traces)
  (let ((oper (trace-lookup cur-trace oper)))
    (cond ((primitive? oper)
           (let ((sim (primitive-simulate oper)))
             (let ((arguments (map (lambda (o)
                                   (traces-lookup (cons cur-trace read-traces) o))
                                 opands)))
               ;; TODO Density
               ((access apply system-global-environment) sim arguments))))
          ((compound? oper)
           (let ((formals (compound-formals oper))
                 (body (compound-body oper))
                 (env (compound-env oper))
                 (trace (compound-trace oper))
                 (read-traces (compound-read-traces oper)))
             (let ((env* (extend-env env formals opands))
                   (trace* cur-trace)
                   ;; Hm.  This strategy means that addresses do not
                   ;; directly depend on which compound got applied,
                   ;; so if the operator changes, I will still have
                   ;; the same addresses in the new body (until the
                   ;; evaluation structure of the bodies diverges).
                   (addr* (extend-address addr 'app))
                   ;; This way, a compound procedure does not carry
                   ;; write permission to the trace in which it was
                   ;; created
                   (read-traces* (cons trace read-traces)))
               (eval body env* trace* addr* read-traces*)))))))

(define (top-eval exp)
  (eval exp (make-env-frame #f '() '()) (rdb-empty) (toplevel-address) '()))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;; Environments

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

;;; Traces

(define (trace-lookup trace addr)
  (trace-search trace addr (lambda (v) v)
   (lambda () (error "Address not found" addr))))

(define (traces-lookup traces addr)
  (let loop ((traces traces))
    (if (null? traces)
        (error "Address not found" addr)
        (trace-search (car traces) addr (lambda (v) v)
         (lambda () (loop (cdr traces)))))))

;;; Pluggable trace interface

(define (trace-search trace addr win lose)
  (cond ((rdb? trace)
         (rdb-trace-search trace addr win lose))
        ;; Poor man's dynamic dispatch system
        (else (lose))))

(define (record! trace exp env addr read-traces answer)
  (cond ((rdb? trace)
         (rdb-record! trace exp env addr read-traces answer))
        (else (error "Unknown trace type" trace))))

(define (trace-extend trace)
  (cond ((rdb? trace)
         (rdb-extend trace))
        (else (error "Unknown trace type" trace))))

;;; Addresses

(define (toplevel-address) (make-address))
(define (extend-address addr step)
  (extend-address-uncurried (cons addr step)))
(define (memoize-in-hash-table table f)
  (lambda (x)
    ;; Not hash-table/intern! because f may modify the table (for
    ;; instance, by recurring through the memoization).
    (hash-table/lookup table x
     (lambda (datum) datum)
     (lambda ()
       (abegin1 (f x) (hash-table/put! table x it))))))
(define extend-address-uncurried (memoize-in-hash-table (make-equal-hash-table) (lambda (x) (make-address))))

;;; Host interface

(define (scheme->venture thing)
  (if (procedure? thing)
      (make-primitive thing #f) ; Don't know the density
      thing)) ; Represent everything else by itself
