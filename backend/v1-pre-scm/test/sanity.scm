(define inference-smoke-test-defn
  `(begin
     (define model-trace (rdb-extend (get-current-trace)))
     (trace-in model-trace
               (begin
                 (define x (flip))
                 x))
     (pp (trace-in (store-extend model-trace) x))
     (mcmc-step model-trace)
     (trace-in (store-extend model-trace) x)))

;; We can flip different choices

(define inference-smoke-test-2-defn
  `(begin
     (define model-trace (rdb-extend (get-current-trace)))
     (trace-in model-trace
               (begin (define x1 (flip))
                      (define x2 (flip))))
     ,map-defn
     (map (lambda (i)
            (begin
              (pp (trace-in (store-extend model-trace) (list x1 x2)))
              (mcmc-step model-trace)))
          '(1 2 3 4))
     (trace-in (store-extend model-trace) (list x1 x2))))

(define-each-check
  (equal? (top-eval 1) 1)
  (equal? (top-eval '((lambda () 1))) 1)
  (equal? (top-eval '((lambda (x) 1) 2)) 1)
  (equal? (top-eval '((lambda (x) x) 2)) 2)
  (equal? (top-eval '((lambda (x) (atomically x)) 3)) 3)
  (equal? (top-eval '((atomically (lambda (x) (atomically x))) 4)) 4)
  (equal? (top-eval '(+ 3 2)) 5)
  (equal? (top-eval '(((lambda (x) (lambda (y) (+ x y))) 3) 4)) 7)
  (equal? (top-eval '(((lambda (x) (atomically (lambda (y) (+ x y)))) 3) 4)) 7)
  (equal? (top-eval '(begin (+ 2 3) (* 2 3))) 6)
  (equal? (top-eval
           `(begin
              ,map-defn
              (map (lambda (x) (+ x 1)) (list 1 2 3))))
          '(2 3 4))
  (equal? (top-eval '(prim-map (lambda (x) (+ x 1)) '(1 2 3 4))) '(2 3 4 5))
  (boolean? (top-eval inference-smoke-test-defn))
  ((lambda (items)
     (and (boolean? (car items))
          (boolean? (cadr items)))) (top-eval inference-smoke-test-2-defn))
  (equal? (top-eval '(model-in (rdb-extend (get-current-trace))
                               (assume x 4)
                               (predict x))) 4)
  (equal? (top-eval `((,(lambda () (lambda () 5))))) 5) ;; Foreign procedures returning procedures
  )

(define-test (absorption-suppresses-resimulation)
  (let ((resim-count (list 0))
        (assess-count (list 0)))
    (top-eval
     `(begin
        ,map-defn
        ,mcmc-defn
        (define my-sim
          (make-sp
           (lambda ()
             (set-car! ',resim-count (+ (car ',resim-count) 1))
             1)
           (lambda (val)
             (set-car! ',assess-count (+ (car ',assess-count) 1))
             0)))
        (model-in (rdb-extend (get-current-trace))
          (assume x (my-sim))
          (assume y (my-sim))
          (infer (mcmc 5)))))
    ;; Two simulations for the initial forward run, zero when
    ;; enforcing constraints, plus one (not two) per mcmc step.
    (check (= (car resim-count) 7))
    ;; Two assessments for each non-resimulated application during
    ;; inference (one in the new trace and one in the old), and two
    ;; assessments for each application during constraint enforcement.
    (check (= (car assess-count) 14))))

(define-test (absorption-suppresses-resimulation-traced-sp)
  (let ((resim-count (list 0))
        (assess-count (list 0)))
    (top-eval
     `(begin
        ,map-defn
        ,mcmc-defn
        (model-in (rdb-extend (get-current-trace))
          (assume my-sim
            (make-sp
             (lambda ()
               (set-car! ',resim-count (+ (car ',resim-count) 1))
               1)
             (lambda (val)
               (set-car! ',assess-count (+ (car ',assess-count) 1))
               0)))
          (assume x (my-sim))
          (assume y (my-sim))
          (infer (mcmc 5)))))
    ;; Two simulations for the initial forward run, zero when
    ;; enforcing constraints, plus one (not two) per mcmc step.
    (check (= (car resim-count) 7))
    ;; Two assessments for each non-resimulated application during
    ;; inference (one in the new trace and one in the old), and two
    ;; assessments for each application during constraint enforcement.
    (check (= (car assess-count) 14))))

(define-test (inference-mixing-smoke)
  (let ()
    (define program
      `(begin
         ,map-defn
         ,mcmc-defn
         (model-in (rdb-extend (get-current-trace))
           (assume x (flip 1/2))
           (let ((pre-inf (predict x)))
             (infer (mcmc 1))
             (cons pre-inf (predict x))))))
    (check (> (chi-sq-test (collect-samples program)
                           '(((#t . #t) . 1/4) ((#t . #f) . 1/4)
                             ((#f . #t) . 1/4) ((#f . #f) . 1/4)))
              *p-value-tolerance*))))

(define-test (coupled-assessability-leads-to-absorption)
  (let ((sim-count (list 0))
        (assess-count (list 0)))
    (top-eval
      `(begin
         ,map-defn
         ,mcmc-defn
         (define my-sim
           (annotate
            (lambda ()
              (set-car! ',sim-count (+ (car ',sim-count) 1))
              1)
            coupled-assessor-tag
            (make-coupled-assessor
             (lambda () '())
             (lambda (x) 'ok)
             (lambda (val state)
               (set-car! ',assess-count (+ (car ',assess-count) 1))
               (cons 0 '())))))
         (model-in (rdb-extend (get-current-trace))
           (assume x (my-sim))
           (assume y (my-sim))
           (infer (mcmc 5)))))
    ;; Two simulations for the initial forward run, zero when
    ;; enforcing constraints, plus one (not two) per mcmc step.
    (check (= (car sim-count) 7))
    ;; Two assessments for each non-resimulated application during
    ;; inference (one in the new trace and one in the old), and two
    ;; assessments for each application during constraint enforcement.
    (check (= (car assess-count) 14))))
