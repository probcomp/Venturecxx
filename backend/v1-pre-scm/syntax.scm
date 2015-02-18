(declare (usual-integrations))

;;; Syntax

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
(define-algebraic-matcher lambda-form lambda-form? cadr cddr)

(define trace-in-form? (tagged-list? 'trace-in))
(define-algebraic-matcher trace-in-form trace-in-form? cadr caddr)

(define (application-form? thing)
  (and (pair? thing)
       (not (or (constant? thing)
                (begin-form? thing)
                (definition? thing)
                (var? thing)
                (if-form? thing)
                (lambda-form? thing)
                (trace-in-form? thing)
                (operative-form? thing)))))
(define-algebraic-matcher application-form application-form? car cdr)

;;; Special forms Kernel-style

(define-structure (operative (safe-accessors #t)) procedure)
(define operatives '())

(define-integrable (operative-form form win lose)
  (if (pair? form)
      (aif (assq (car form) operatives)
           (win (cdr it) (cdr form))
           (lose))
      (lose)))

(define (operative-form? form)
  (operative-form form (lambda (oper opands) #t) (lambda () #f)))

(define (register-operative! name operative)
  (set! operatives (cons (cons name operative) operatives)))

(define-syntax define-operative
  (syntax-rules ()
    ((_ (name arg ...) body ...)
     (register-operative! 'name (make-operative (lambda (arg ...) body ...))))))

;; Permit reflection on the evaluation context

(define-operative (get-current-environment subforms env trace addr read-traces) env)
(define-operative (get-current-trace subforms env trace addr read-traces) trace)
(define-operative (get-current-read-traces subforms env trace addr read-traces) read-traces)

;; Macros for model-inference style (i.e., Venture v0)

(define *the-model-trace* #f)
(define *the-model-env* #f)

(define-operative (model-in subforms env trace addr read-traces)
  (let ((trace-subform (car subforms))
        (body-forms (cdr subforms)))
    ;; Can I get away with using MIT Scheme's native fluid-let here,
    ;; or do I need to do this in the object language?
    (fluid-let ((*the-model-trace*
                 (eval trace-subform env trace (extend-address addr 'model-in) read-traces))
                (*the-model-env* (extend-env env '() '())))
      (eval `(begin ,@body-forms) env trace (extend-address addr 'model-in-body) read-traces))))

(define-operative (assume subforms env trace addr read-traces)
  (eval `(trace-in ,*the-model-trace* (define ,(car subforms) ,(cadr subforms)))
        *the-model-env* trace addr read-traces))

(define-operative (observe subforms env trace addr read-traces)
  (eval `(trace-in ,*the-model-trace* ($observe ,(car subforms) ,(cadr subforms)))
        *the-model-env* trace addr read-traces))

(define-operative (infer subforms env trace addr read-traces)
  (eval `(,(car subforms) ,*the-model-trace*)
        env trace addr read-traces))

(define-operative (predict subforms env trace addr read-traces)
  (eval `(trace-in ,*the-model-trace* ,(car subforms))
        *the-model-env* trace addr read-traces))

;; Example of using the argument language syntax

(define (trick-coin-example-raw)
  `(begin
     ,observe-defn
     ,map-defn
     (define model-trace (rdb-extend (get-current-trace)))
     (trace-in model-trace
               (begin
                 (define is-trick? (flip 0.5))
                 (define weight (if is-trick? (uniform 0 1) 0.5))
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 (define answer (list is-trick? weight))))
     (enforce-constraints model-trace)
     (map (lambda (i) (mcmc-step model-trace))
          '(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20))
     (trace-in (store-extend model-trace) answer)))

(define (trick-coin-example-syntax)
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume is-trick? (flip 0.5))
       (assume weight (if is-trick? (uniform 0 1) 0.5))
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (infer (mcmc 20))
       (predict (list is-trick? weight)))))

;; Other syntax

(define-operative (atomically subforms env trace addr read-traces)
  ;; Hm.  It seems a little redundant to eval a trace-in form in the
  ;; current trace.  Maybe I should actually abstract the notion of a
  ;; macro, instead of slavishly adhering to a coding style to expose
  ;; macroness.
  (eval `(trace-in ,(store-extend trace) ,(car subforms))
        env trace addr read-traces))

(define-operative (let subforms env trace addr read-traces)
  (let ((bindings (car subforms))
        (body (cdr subforms)))
    (eval `((lambda (,@(map car bindings))
              ,@body)
            ,@(map cadr bindings))
          env trace addr read-traces)))
