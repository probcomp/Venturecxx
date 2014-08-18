(declare (usual-integrations))

(define-structure (trace (safe-accessors #t))
  parent
  addresses
  values) ; Parallel lists mapping addresses to values, and possible metadata

(define-structure (env-frame (safe-accessors #t))
  parent
  symbols
  addresses) ; Parallel lists mapping symbols to addresses

(define-structure (compound (safe-accessors #t))
  formals
  body
  env
  trace
  read-traces)

(define-structure primitive) ; What's in primitive procedures?

(define-structure address) ; Contentless structure with only identity
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

(define (eval exp env trace addr read-traces)
  (at-address trace addr
   (lambda ()
     (do-eval exp env trace read-traces))))

(define (do-eval exp env trace read-traces)
  (cond ((constant? exp)
         (constant-value exp))
        ((variable? exp)
         (let ((addr (env-lookup env exp)))
           (traces-lookup (cons trace read-traces) addr)))
        ((lambda? exp)
         (make-compound
          (lambda-formals exp)
          (lambda-body exp)
          env
          trace
          read-traces))
        ((extend? exp)
         (let ((subtrace (trace-extend trace))
               (addr (fresh-address)))
           ;; Could add trace to read-traces here instead of stashing
           ;; it in the parent pointer
           (eval exp env subtrace addr read-traces)))
        (else ;; Application
         (let ((subvals (map (lambda (e)
                               (let ((addr (fresh-address)))
                                 (eval e env trace addr read-traces)))
                             (subforms exp))))
           (apply (car subvals) (cdr subvals) trace)))))

(define (apply oper opands cur-trace)
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
             (eval body env* trace* addr* read-traces*))))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (env-lookup env symbol)
  (if (env-frame? env)
      (let loop ((ss (env-frame-symbols env))
                 (as (env-frame-addresses env)))
        (cond ((null? ss)
               (env-lookup (env-frame-parent env) symbol))
              ((eq? (car ss) symbol)
               (car as))
              (else (loop (cdr ss) (cdr as)))))
      (error "Symbol not found" symbol)))
(define extend-env make-env-frame)

(define (trace-search trace addr win lose)
  (if (trace? trace)
      (trace-search-one trace addr win
       (lambda () (trace-search (trace-parent trace) addr win lose)))
      (lose)))

(define (trace-lookup trace addr)
  (trace-search trace addr (lambda (v) v)
   (lambda () (error "Symbol not found" symbol))))

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

(define (subforms exp) exp)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; VKM's pronouncements:

;;; Traces are things by which an execution can be reconstructed even
;;; in the presence of random choice.

;;; The only way you get to allocate mutable storage is if you have
;;; written a program whose space of executions defines the set of all
;;; valid values that can be stored.
