(declare (usual-integrations eval apply))
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

(define-structure (address (constructor %make-address))
  index) ;; Sortable by creation time

(define next-address 0)
(define (make-address)
  (set! next-address (+ next-address 1))
  (%make-address next-address))
(define-integrable (address<? a1 a2)
  (< (address-index a1) (address-index a2)))
(define address-wt-tree-type (make-wt-tree-type address<?))
(define (make-address-wt-tree)
  (make-wt-tree address-wt-tree-type))

;; A standard lexical environment structure; holds addresses into
;; traces rather than values.
(define-structure (env-frame (safe-accessors #t))
  parent
  symbols
  addresses) ; Parallel lists mapping symbols to addresses

;;; Procedures

(define-structure (foreign (safe-accessors #t)) simulate)

(define-structure (compound (safe-accessors #t))
  formals
  body
  env
  trace
  read-traces)

;;; Requests

;; Requests are an evaluation trampoline available to allow foreign
;; procedures (and incidentally everything else in the language) to
;; call Venture procedures in the foreign procedure's call site's
;; evaluation context.

(define-structure (evaluation-request (safe-accessors #t))
  exp env cont)

(define-structure (application-request (safe-accessors #t))
  operator operands cont)

;;; Data with metadata

;; Annotated val ann = Annotated val [(Tag, ann)]

;; TODO Do I want to enforce the invariant that all annotated objects
;; are flattened, to wit that the base of any annotated thing is not
;; itself annotated?  Do I want to pretend that's so by abstraction
;; barriers?
(define-structure (annotated (safe-accessors #t)) base annotations)

(define-structure annotation-tag) ; Opaque, unique

(define ((has-annotation? tag) thing)
  (and (annotated? thing)
       (or (assq tag (annotated-annotations thing))
           ((has-annotation? tag) (annotated-base thing)))))

(define ((annotation-of tag) thing)
  (aif ((has-annotation? tag) thing)
       (cdr it)
       (error "No annotation on" thing tag)))

(define (annotate thing tag value)
  (if (annotated? thing)
      (make-annotated (annotated-base thing) (cons (cons tag value) (annotated-annotations thing)))
      (make-annotated thing `((,tag . ,value)))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;; Essential evaluation

(define (eval exp env trace addr read-traces)
  ;; TODO What happens if this address is recorded, but not in the
  ;; current trace?
  (ensure (or/c env-frame? false?) env)
  (ensure address? addr)
  (resolve-request
   (trace-search trace addr (lambda (v) v)
    (lambda ()
      ;; The trace can decide whether to invoke the "evaluate
      ;; normally" continuation, and if so, can intercept and modify
      ;; the answer.  The trace is expected to record said result at
      ;; the address (so it can be looked up from environments).
      (trace-eval! trace exp env addr read-traces
        (lambda ()
          (do-eval exp env trace addr read-traces)))))
   trace addr read-traces))

(define (do-eval exp env trace addr read-traces)
  (case* exp
    ((constant val) (scheme->venture val))
    ((var x)
     (env-search env x
      (lambda (addr)
        (traces-lookup (cons trace read-traces) addr))
      (lambda ()
        (scheme->venture
         (environment-lookup user-initial-environment x)))))
    ((lambda-form formals body)
     ;; Do I need to close over the maker address?
     (make-compound formals body env trace read-traces))
    ((trace-in-form trace-form subform)
     (let ((subtrace (eval trace-form env trace (extend-address addr '(trace-in trace)) read-traces)))
       (eval subform env subtrace (extend-address addr '(trace-in form)) read-traces)))
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
    ((operative-form operative subforms)
     ((operative-procedure operative) subforms env trace addr read-traces))
    (_ ;; Application
     (let ((subaddrs (map (lambda (e i)
                            (let ((addr* (extend-address addr `(app-sub ,i))))
                              (eval e env trace addr* read-traces)
                              addr*))
                          exp ; The subforms
                          (iota (length exp)))))
       (apply (trace-lookup trace (car subaddrs)) (cdr subaddrs) addr trace read-traces)))))

;; Takes the operator, the addresses of the operands, the address of
;; the application itself, the current trace, and the list of readable
;; traces.
(define (apply oper opand-addrs addr cur-trace read-traces)
  (cond ((foreign? oper)
         ((foreign-simulate oper) oper opand-addrs addr cur-trace read-traces))
        ((compound? oper)
         (apply-compound oper opand-addrs addr cur-trace read-traces))
        ((annotated? oper)
         (apply-annotated oper opand-addrs addr cur-trace read-traces))
        (else
         (error "Inapplicable object" oper))))

(define (apply-compound oper opand-addrs addr cur-trace read-traces)
  (let ((formals (compound-formals oper))
        (body (compound-body oper))
        (env (compound-env oper))
        (trace (compound-trace oper))
        (read-traces (compound-read-traces oper)))
    (let ((env* (extend-env env formals opand-addrs))
          (trace* cur-trace)
          ;; Hm.  This strategy means that addresses do not directly
          ;; depend on which compound got applied, so if the operator
          ;; changes, I will still have the same addresses in the new
          ;; body (until the evaluation structure of the bodies
          ;; diverges).
          ;; TODO Is that actually a bug, where old values preempt new?
          (addr* (extend-address addr 'app))
          ;; This way, a compound procedure does not carry write
          ;; permission to the trace in which it was created

          ;; TODO Include the read-traces passed to apply?  Why not?
          ;; Is there an invariant that nothing from the closure's
          ;; body can ever refer to any trace that the closure is not
          ;; closed over?
          (read-traces* (cons trace read-traces)))
      (eval body env* trace* addr* read-traces*))))

(define (apply-annotated oper opand-addrs addr cur-trace read-traces)
  ;; There is a choice between store-extending the current trace and
  ;; not extending it.  Extending effectively makes all assessable
  ;; objects hide their internals from the caller (of course, this
  ;; does not prevent said internals from tracing something if they
  ;; want, by further extending).

  ;; In principle, this could be written not to extend, and "mu" could
  ;; be written to insert a request to store-extend the bodies of
  ;; assessable procedures.  The natural way to do that is impeded
  ;; because variadic lambdas seem to be a pain to provide in this
  ;; language (except maybe with a restriction that the only thing one
  ;; can do with an argument list is apply something else to it?).
  (let ((sub-trace (store-extend cur-trace)))
    ;; By calling apply rather than eval, I elide recording the
    ;; identity function that transports the result of the simulator
    ;; to the result of the whole SP.
    (apply (annotated-base oper) opand-addrs addr sub-trace read-traces)))

;; This is different from "apply" because it records the evaluation in
;; the trace.
(define (eval-application operator operands addr trace read-traces)
  (eval `(,@(map (lambda (thing) `(quote ,thing))
                 (cons operator operands)))
        #f ; Env of an application with pre-evaluated parts should be ignored anyway
        trace
        addr
        read-traces))

(define (resolve-request maybe-request trace requester-addr read-traces)
  (define (continue k results)
    (eval-application
     k results
     ;; TODO This means the address does not depend on the
     ;; continuation of the request.  Is that a problem?
     (extend-address requester-addr 'continue)
     trace read-traces))
  (cond ((evaluation-request? maybe-request)
         (continue
          (evaluation-request-cont maybe-request)
          (list
           (eval (evaluation-request-exp maybe-request)
                 (evaluation-request-env maybe-request)
                 trace
                 ;; TODO This means the address does not depend on the
                 ;; content of the request.  Is that a problem?
                 (extend-address requester-addr 'request)
                 read-traces))))
        ((application-request? maybe-request)
         (continue
          (application-request-cont maybe-request)
          (list
           (eval-application
            (application-request-operator maybe-request)
            (application-request-operands maybe-request)
            ;; TODO This means the address does not depend on the
            ;; content of the request.  Is that a problem?
            (extend-address requester-addr 'request)
            trace read-traces))))
        (else ; Wasn't a request
         maybe-request)))

(define (top-eval exp)
  (eval exp (make-env-frame #f '() '()) (store-extend #f) (toplevel-address) '()))

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
(define (extend-env parent symbols addresses)
  (ensure (or/c env-frame? false?) parent)
  (ensure (listof symbol?) symbols)
  (ensure (listof address?) addresses)
  (make-env-frame parent symbols addresses))
(define (env-bind! env sym addr)
  (ensure env-frame? env)
  (ensure symbol? sym)
  (ensure address? addr)
  (set-env-frame-symbols! env (cons sym (env-frame-symbols env)))
  (set-env-frame-addresses! env (cons addr (env-frame-addresses env))))
(define (env-lookup env symbol)
  (ensure (or/c env-frame? false?) env)
  (ensure symbol? symbol)
  (env-search env symbol (lambda (a) a) (lambda () #f)))

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
  (ensure address? addr)
  (cond ((rdb? trace)
         (rdb-trace-search trace addr win lose))
        ;; Poor man's dynamic dispatch system
        ((store? trace)
         (store-trace-search trace addr win lose))
        (else (lose))))

(define (trace-eval! trace exp env addr read-traces continue)
  (cond ((rdb? trace)
         (rdb-trace-eval! trace exp env addr read-traces continue))
        ((store? trace)
         (store-trace-eval! trace exp env addr read-traces continue))
        (else (error "Unknown trace type" trace))))

(define (record-constraint! trace addr value)
  (cond ((rdb? trace)
         (rdb-record-constraint! trace addr value))
        ((store? trace)
         (store-record-constraint! trace addr value))
        (else (error "Unknown trace type" trace))))

;;; One hack: allow PETs but do not allow them to be extended.  Then
;;; we should be able to grandfather in all our old code.

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
      (scheme-procedure-over-values->v1-foreign thing)
      ;; TODO Actually, I should recur on containers, to catch any
      ;; procedures hiding in them
      thing)) ; Represent everything else by itself

(define (scheme-procedure-over-values->v1-foreign sim)
  (make-foreign
   (lambda (oper opand-addrs addr cur-trace read-traces)
     (let ((arguments (map (lambda (o)
                             (traces-lookup (cons cur-trace read-traces) o))
                           opand-addrs)))
       (scheme->venture (scheme-apply sim arguments))))))

(define (scheme-procedure-over-addresses->v1-foreign sim)
  (make-foreign
   (lambda (oper opand-addrs addr cur-trace read-traces)
     (scheme->venture (scheme-apply sim opand-addrs)))))
