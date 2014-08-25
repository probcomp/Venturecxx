(declare (usual-integrations))

;;; Exploratory programming on the subject of the essence of a
;;; computation being able to reflect on and modify its own value
;;; history.

;; A value history; maybe this should be called "store" since it does
;; not retain any information about what the value is about.
(define-structure (trace (safe-accessors #t))
  parent
  addresses
  values) ; Parallel lists mapping addresses to values

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
  trace ; Empirically, they want to close over their traces
  read-traces)

(define-structure primitive) ; What's in primitive procedures?

(define-structure address) ; Contentless structure with only identity for addressing traces
(define (fresh-address) (make-address))

(define (at-address trace addr thunk)
  (trace-search-one trace addr (lambda (v) v)
   (lambda ()
     (let ((answer (thunk)))
       ;; And maybe metadata depending on what kind of trace it is.
       ;; The metadata is presumably dependent on the structure of
       ;; the thunk, so this abstraction will not endure
       (trace-store! trace addr answer)
       answer))))

;; The evaluation context includes a current trace (into which
;; evaluation is being recorded) and a set of additional traces
;; (whence values are read).  The additional traces arise because the
;; trace a closure holds needs to be available when evaluating its
;; body, even if that evaluation occurs in a different trace from the
;; one(s) captured by the closure.  Perhaps these extras can be stored
;; in the new lexical enviornment frame to good effect.

;; One might enforce the discipline that the traces eval reads from
;; are not to be written to even reflectively.  Or not.
(define (eval exp env trace addr read-traces)
  (at-address trace addr
   (lambda ()
     (do-eval exp env trace read-traces))))

(define (do-eval exp env trace read-traces)
  (cond ((constant? exp)
         (constant-value exp))
        ((variable? exp)
         (env-search env exp
           (lambda (addr)
             (traces-lookup (cons trace read-traces) addr))
           (lambda ()
             ((access eval system-global-environment) exp user-initial-environment))))
        ((lambda? exp)
         (make-compound
          (lambda-formals exp)
          (lambda-body exp)
          env
          trace
          read-traces))
        ;; Interesting new operation: evaluate in a subtrace.  Adding
        ;; a new trace frame like this hides the nested evaluation
        ;; from appearing in the current trace, and can shield the
        ;; current trace from reflective changes made to the nexted
        ;; one if the trace modification policy enforces that.
        ((extend? exp)
         (let ((subtrace (trace-extend trace))
               (addr (fresh-address)))
           ;; Could add trace to read-traces here instead of stashing
           ;; it in the parent pointer
           (eval (ext-subexp exp) env subtrace addr read-traces)))
        ;; Permit reflection on the evaluation context
        ((nullary? 'get-current-environment exp) env)
        ((nullary? 'get-current-trace exp) trace)
        ((nullary? 'get-current-read-traces exp) read-traces)
        ((define? exp)
         (let ((addr (fresh-address)))
           (eval (caddr exp) env trace addr read-traces)
           (env-bind! env (cadr exp) addr)))
        ((if? exp)
         (if (eval (cadr exp)   env trace (fresh-address) read-traces)
             (eval (caddr exp)  env trace (fresh-address) read-traces)
             (eval (cadddr exp) env trace (fresh-address) read-traces)))
        ((begin? exp)
         (let ()
           (define result #f)
           (for-each
            (lambda (s)
              (let ((addr (fresh-address)))
                (set! result (eval s env trace addr read-traces))))
            (cdr (subforms exp)))     ; cdr excludes the 'begin symbol
           result))
        (else ;; Application
         (let ((subaddrs (map (lambda (e)
                               (let ((addr (fresh-address)))
                                 (eval e env trace addr read-traces)
                                 addr))
                             (subforms exp))))
           (apply (car subaddrs) (cdr subaddrs) trace read-traces)))))

(define (apply oper opands cur-trace read-traces)
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
                   (addr* (fresh-address))
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
      (lose)
      #;(error "Symbol not found" symbol)))
(define extend-env make-env-frame)
(define (env-bind! env sym addr)
  (set-env-frame-symbols! env (cons sym (env-frame-symbols env)))
  (set-env-frame-addresses! env (cons addr (env-frame-addresses env))))

(define (trace-search trace addr win lose)
  (if (trace? trace)
      (trace-search-one trace addr win
       (lambda () (trace-search (trace-parent trace) addr win lose)))
      (lose)))

(define (trace-lookup trace addr)
  (trace-search trace addr (lambda (v) v)
   (lambda () (error "Address not found" addr))))

(define (traces-lookup traces addr)
  (let loop ((traces traces))
    (if (null? traces)
        (error "Address not found" addr)
        (trace-search (car traces) addr (lambda (v) v)
         (lambda () (loop (cdr traces)))))))

(define (trace-search-one trace addr win lose)
  (let loop ((as (trace-addresses trace))
             (vs (trace-values trace)))
    (cond ((null? as)
           (lose))
          ((eq? (car as) addr)
           (win (car vs)))
          (else (loop (cdr as) (cdr vs))))))

(define (trace-store! trace addr val)
  (set-trace-addresses! trace (cons addr (trace-addresses trace)))
  (set-trace-values! trace (cons val (trace-values trace))))

(define (trace-extend trace)
  (make-trace trace '() '()))

(define (top-eval exp)
  (eval exp (make-env-frame #f '() '()) (make-trace #f '() '()) (fresh-address) '()))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Expressions

(define (constant? exp)
  (and (not (symbol? exp))
       (or (not (pair? exp))
           (eq? (car exp) 'quote))))

(define (constant-value exp)
  (if (pair? exp)
      (cadr exp)
      exp))

(define variable? symbol?)

(define (lambda? exp)
  (and (pair? exp) (eq? (car exp) 'lambda)))

(define lambda-formals cadr)
(define lambda-body caddr)

(define (extend? exp)
  (and (pair? exp) (eq? (car exp) 'ext)))
(define ext-subexp cadr)

(define (begin? exp)
  (and (pair? exp) (eq? (car exp) 'begin)))

(define (define? exp)
  (and (pair? exp) (eq? (car exp) 'define)))

(define (if? exp)
  (and (pair? exp) (eq? (car exp) 'if)))

(define (subforms exp) exp)

(define (nullary? symbol exp)
  (and (pair? exp) (null? (cdr exp)) (eq? symbol (car exp))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Test cases

; 1 => 1
; '((lambda () 1)) => 1
; '((lambda (x) 1) 2) => 1
; '((lambda (x) x) 2) => 2
; '((lambda (x) (ext x)) 3) => 3
; '((ext (lambda (x) (ext x))) 4) => 4
; '(+ 3 2) => 5
; '(((lambda (x) (lambda (y) (+ x y))) 3) 4) => 7
; '(((lambda (x) (ext (lambda (y) (+ x y)))) 3) 4) => 7
; '(begin (+ 2 3) (* 2 3)) => 6
#;
 '((lambda (addr)
     (begin
       (trace-store! (get-current-trace) addr 8)
       (env-bind! (get-current-environment) 'x addr)
       x))
   (fresh-address)) ; => 8

(define map-defn
  '(define map
     (lambda (f lst)
       (if (pair? lst)
           (cons (f (car lst)) (map f (cdr lst)))
           lst))))

#;
`(begin
   ,map-defn
   (map (lambda (x) (+ x 1)) (list 1 2 3))) ; => (2 3 4)

(define frobnicate-defn
  '(define frobnicate
     (lambda (trace)
       (set-trace-values! trace
         (map (lambda (item)
                (if (number? item)
                    (+ item 1)
                    item))
              (trace-values trace))))))

;; Directly frobnicating breaks because the set at the end drops all
;; the additional structure created since the fetch at the beginning
;; of frobnicate.

#;
`(begin
   ,map-defn
   ,frobnicate-defn
   (define x 2)
   (define t (get-current-trace))
   (ext (frobnicate t))
   x) ; => 3

#;
`(begin
   ,map-defn
   ,frobnicate-defn
   (define x 3)
   (define y2
     (ext (begin
            (define y 4)
            (define t (get-current-trace))
            (ext (frobnicate t))
            y)))
   (* x y2)) ; => 15

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; VKM's pronouncements:

;;; Traces are things by which an execution can be reconstructed even
;;; in the presence of random choice.

;;; The only way you get to allocate mutable storage is if you have
;;; written a program whose space of executions defines the set of all
;;; valid values that can be stored.

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; AXCH's pronouncement:

;;; I now think that the part of the problem I had in HS-V1 that would
;;; not be solved by the read-traces mechanism is a dependency
;;; problem.  Specifically:
;;; - dependency tracing; and
;;; - dependency-directed computation order, in the presence of
;;;   potential runtime discovery of new dependencies.  (Which
;;;   manifests as the possibility that a value newly discovered to be
;;;   needed may be unregenerated.)
