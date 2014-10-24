(define weighted-coin-flipping-example
  `(begin
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.2))
       (infer (mcmc 100))
       (predict c1))))

(define-test (resimulation-should-always-accept-unconstrained-proposals)
  ;; This manifested as a bug because I wasn't canceling the
  ;; probability of proposing from the prior against the prior's
  ;; contribution to the posterior.
  (fluid-let ((*resimulation-mh-reject-hook* (lambda () (assert-true #f))))
    (top-eval weighted-coin-flipping-example)))

(define weighted-coin-flipping-example-with-spurious-observations
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.2))
       (observe (flip 0.5) #t)
       (observe (flip 0.5) #t)
       (observe (flip 0.5) #t)
       (observe (flip 0.5) #t)
       (observe (flip 0.5) #t)
       (infer (mcmc 100))
       (predict c1))))

(define-test (resimulation-should-always-accept-unconstrained-proposals-even-with-spurious-observations)
  ;; This would manifest as a bug if observations were miscounted as
  ;; random choices in one place but not another, affecting the
  ;; acceptance ratio correction.
  (fluid-let ((*resimulation-mh-reject-hook* (lambda () (assert-true #f))))
    (top-eval weighted-coin-flipping-example-with-spurious-observations)))

(define (constrained-coin-flipping-example inference)
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.5))
       (observe (flip (if c1 1 0.0001)) #t)
       (infer ,inference)
       (predict c1))))

(define-test (constrained-coin-dist)
  (let ()
    (check (> (chi-sq-test (collect-samples (constrained-coin-flipping-example '(mcmc 20)))
                           '((#t . 1) (#f . 1e-4))) *p-value-tolerance*))))

(define-test (constrained-coin-dist-rejection)
  (let ()
    (check (> (chi-sq-test (collect-samples (constrained-coin-flipping-example 'rejection))
                           '((#t . 1) (#f . 1e-4))) *p-value-tolerance*))))

(define (two-coin-flipping-example inference)
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.5))
       (assume c2 (flip 0.5))
       (observe (flip (if (boolean/or c1 c2) 1 0.0001)) #t)
       (infer ,inference)
       (predict c1))))

(define-test (two-coin-dist)
  (let ()
    (check (> (chi-sq-test (collect-samples (two-coin-flipping-example '(mcmc 20)))
                           '((#t . 2/3) (#f . 1/3))) *p-value-tolerance*))))

(define-test (two-coin-dist-rejection)
  (let ()
    (check (> (chi-sq-test (collect-samples (two-coin-flipping-example 'rejection))
                           '((#t . 2/3) (#f . 1/3))) *p-value-tolerance*))))

(define (two-coins-with-brush-example inference)
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.5))
       (assume c2 (if c1 #t (flip 0.5)))
       ; (predict (pp (list c1 c2)))
       (observe (flip (if (boolean/or c1 c2) 1 0.0001)) #t)
       (infer ,inference)
       (predict c1))))

(define-test (two-coin-brush-dist)
  (let ()
    (check (> (chi-sq-test (collect-samples (two-coins-with-brush-example '(mcmc 20)))
                           '((#t . 2/3) (#f . 1/3))) *p-value-tolerance*))))

(define-test (two-coin-brush-dist-rejection)
  (let ()
    (check (> (chi-sq-test (collect-samples (two-coins-with-brush-example 'rejection))
                           '((#t . 2/3) (#f . 1/3))) *p-value-tolerance*))))

(define (two-mu-coins-with-brush-example inference)
  `(begin
     ,observe-defn
     ,mu-flip-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (mu-flip 0.5))
       (assume c2 (if c1 #t (mu-flip 0.5)))
       (observe (mu-flip (if (boolean/or c1 c2) 1 0.0001)) #t)
       (infer ,inference)
       (predict c1))))

(define-test (two-mu-coin-brush-dist)
  (let ()
    (check (> (chi-sq-test (collect-samples (two-mu-coins-with-brush-example '(mcmc 20)))
                           '((#t . 2/3) (#f . 1/3))) *p-value-tolerance*))))

(define-test (two-mu-coin-brush-dist-rejection)
  (let ()
    (check (> (chi-sq-test (collect-samples (two-mu-coins-with-brush-example 'rejection))
                           '((#t . 2/3) (#f . 1/3))) *p-value-tolerance*))))

(define-test (uncollapsed-beta-bernoulli)
  (let ()
    (define program
      `(begin
         ,map-defn
         ,mcmc-defn
         ,observe-defn
         (model-in (rdb-extend (get-current-trace))
           (assume make-uncollapsed-uniform-bernoulli
             (lambda ()
               ((lambda (weight)
                  (lambda ()
                    (flip weight)))
                (uniform 0 1))))
           (assume coin (make-uncollapsed-uniform-bernoulli))
           (observe (coin) #t)
           (observe (coin) #t)
           (observe (coin) #t)
           (assume predictive (coin))
           (infer rdb-backpropagate-constraints!)
           (infer (mcmc 20))
           (predict predictive))))
    (check (> (chi-sq-test (collect-samples program)
                           '((#t . 4/5) (#f . 1/5))) *p-value-tolerance*))))

(define-test (collapsed-beta-bernoulli)
  (let ()
    (define program
      `(begin
         ,observe-defn
         (model-in (rdb-extend (get-current-trace))
           (assume make-uniform-bernoulli
             (lambda ()
               ((lambda (aux-box)
                  (lambda ()
                    ((lambda (weight)
                       (begin
                         ((lambda (answer)
                            (begin
                              (trace-in (store-extend (get-current-trace))
                                (if answer
                                    (set-car! aux-box (+ (car aux-box) 1))
                                    (set-cdr! aux-box (+ (cdr aux-box) 1))))
                              answer))
                          (flip weight))))
                     (/ (+ (car aux-box) 1)
                        (+ (car aux-box) (cdr aux-box) 2)))))
                (cons 0 0))))
           (assume coin (make-uniform-bernoulli))
           (observe (coin) #t)
           (observe (coin) #t)
           (observe (coin) #t)
           (infer rdb-backpropagate-constraints!)
           (infer enforce-constraints) ; Note: no mcmc
           ;; Predicting (coin) instead of (assume prediction (coin))
           ;; (infer...) (predict prediction) because
           ;; enforce-constraints respects the originally-sampled
           ;; values, and I want to emphasize that MCMC is not needed
           ;; for a collapsed model.
           (predict (coin)))))
    (check (> (chi-sq-test (collect-samples program)
                           '((#t . 4/5) (#f . 1/5))) *p-value-tolerance*))))

(define-test (uncollapsed-beta-bernoulli-explicitly-assessable)
  (let ()
    (define program
      `(begin
         ,map-defn
         ,mcmc-defn
         ,observe-defn
         (model-in (rdb-extend (get-current-trace))
           (assume make-uncollapsed-uniform-bernoulli
             (lambda ()
               ((lambda (weight)
                  (make-sp
                   (lambda ()
                     (flip weight))
                   (lambda (val)
                     ((assessor-of flip) val weight))))
                (uniform 0 1))))
           (assume coin (make-uncollapsed-uniform-bernoulli))
           (observe (coin) #t)
           (observe (coin) #t)
           (observe (coin) #t)
           (assume predictive (coin))
           ;; Works with and without propagating constraints
           ;; (infer rdb-backpropagate-constraints!)
           (infer (mcmc 20))
           (predict predictive))))
    (check (> (chi-sq-test (collect-samples program)
                           '((#t . 4/5) (#f . 1/5))) *p-value-tolerance*))))

(define-test (collapsed-beta-bernoulli-explicit-assessor)
  (let ()
    (define program
      `(begin
         ,observe-defn
         (model-in (rdb-extend (get-current-trace))
           (assume make-uniform-bernoulli
             (lambda ()
               ((lambda (aux-box)
                  ;; TODO This version is broken because declaring a
                  ;; (full) assessor effectively prevents the body
                  ;; from incorporating the answer.  (In the current
                  ;; RandomDB, the body runs unconstrained and has its
                  ;; side-effect).
                  (annotate
                   (lambda ()
                     ((lambda (weight)
                        (begin
                          ((lambda (answer)
                             (begin
                               (trace-in (store-extend (get-current-trace))
                                 (if answer
                                     (set-car! aux-box (+ (car aux-box) 1))
                                     (set-cdr! aux-box (+ (cdr aux-box) 1))))
                               answer))
                           (flip weight))))
                      (/ (+ (car aux-box) 1)
                         (+ (car aux-box) (cdr aux-box) 2))))
                   coupled-assessor-tag
                   (make-coupled-assessor
                    (lambda () (cons (car aux-box) (cdr aux-box)))
                    (lambda (new-box)
                      (set-car! aux-box (car new-box))
                      (set-cdr! aux-box (cdr new-box)))
                    (lambda (val aux)
                      ((lambda (weight)
                         (cons
                          ((assessor-of flip) val weight)
                          (if val
                              (cons (+ (car aux) 1) (cdr aux))
                              (cons (car aux) (+ (cdr aux) 1)))))
                       (/ (+ (car aux) 1)
                          (+ (car aux) (cdr aux) 2)))))))
                (cons 0 0))))
           (assume coin (make-uniform-bernoulli))
           (observe (coin) #t)
           (observe (coin) #t)
           (observe (coin) #t)
           (infer rdb-backpropagate-constraints!)
           (infer enforce-constraints) ; Note: no mcmc
           ;; Predicting (coin) instead of (assume prediction (coin))
           ;; (infer...) (predict prediction) because
           ;; enforce-constraints respects the originally-sampled
           ;; values, and I want to emphasize that MCMC is not needed
           ;; for a collapsed model.
           (predict (coin)))))
    (check (> (chi-sq-test (collect-samples program)
                           '((#t . 4/5) (#f . 1/5))) *p-value-tolerance*))))
