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

(define (standard-beta-bernoulli-test-program maker-form prediction-program)
  `(begin
     ,map-defn
     ,mcmc-defn
     ,observe-defn
     (model-in (rdb-extend (get-current-trace))
       (assume make-uniform-bernoulli ,maker-form)
       (assume coin (make-uniform-bernoulli))
       (observe (coin) #t)
       (observe (coin) #t)
       (observe (coin) #t)
       ,@prediction-program)))
(define standard-beta-bernoulli-posterior '((#t . 4/5) (#f . 1/5)))

(define (check-beta-bernoulli maker-form prediction-program)
  (check (> (chi-sq-test
             (collect-samples
              (standard-beta-bernoulli-test-program maker-form prediction-program))
             standard-beta-bernoulli-posterior)
            *p-value-tolerance*)))

(define uncollapsed-beta-bernoulli-maker
  '(lambda ()
     (let ((weight (uniform 0 1)))
       (lambda ()
         (flip weight)))))

(define collapsed-beta-bernoulli-maker
  '(lambda ()
     (let ((aux-box (cons 0 0)))
       (lambda ()
         (let ((weight (/ (+ (car aux-box) 1)
                          (+ (car aux-box) (cdr aux-box) 2))))
           (let ((answer (flip weight)))
             (trace-in (store-extend (get-current-trace))
                       (if answer
                           (set-car! aux-box (+ (car aux-box) 1))
                           (set-cdr! aux-box (+ (cdr aux-box) 1))))
             answer))))))

(define uncollapsed-assessable-beta-bernoulli-maker
  '(lambda ()
     (let ((weight (uniform 0 1)))
       (make-sp
        (lambda ()
          (flip weight))
        (annotate
         (lambda (val)
           ((assessor-of flip) val weight))
         value-bound-tag
         (lambda (val)
           (((annotation-of value-bound-tag) (assessor-of flip))
            val weight)))))))

(define collapsed-assessable-beta-bernoulli-maker
  '(lambda ()
     (let ((aux-box (cons 0 0)))
       (annotate
        (lambda ()
          (let ((weight (/ (+ (car aux-box) 1)
                           (+ (car aux-box) (cdr aux-box) 2))))
            (let ((answer (flip weight)))
              ; (pp (list 'simulated answer 'from aux-box weight))
              (trace-in (store-extend (get-current-trace))
                        (if answer
                            (set-car! aux-box (+ (car aux-box) 1))
                            (set-cdr! aux-box (+ (cdr aux-box) 1))))
              answer)))
        coupled-assessor-tag
        (annotate
         (make-coupled-assessor
          (lambda () (cons (car aux-box) (cdr aux-box)))
          (lambda (new-box)
            (set-car! aux-box (car new-box))
            (set-cdr! aux-box (cdr new-box)))
          (lambda (val aux)
            (let ((weight (/ (+ (car aux) 1)
                             (+ (car aux) (cdr aux) 2))))
              (begin
                ; (pp (list 'assessing val aux weight))
                (cons
                 ((assessor-of flip) val weight)
                 (if val
                     (cons (+ (car aux) 1) (cdr aux))
                     (cons (car aux) (+ (cdr aux) 1))))))))
         value-bound-tag
         (lambda (val aux)
           (let ((weight (/ (+ (car aux) 1)
                            (+ (car aux) (cdr aux) 2))))
             (((annotation-of value-bound-tag) (assessor-of flip))
              val weight))))))))

(define-test (uncollapsed-beta-bernoulli)
  (check-beta-bernoulli
   uncollapsed-beta-bernoulli-maker
   '((assume predictive (coin))
     (infer rdb-backpropagate-constraints!)
     (infer (mcmc 20))
     (predict predictive))))

(define-test (uncollapsed-beta-bernoulli-rejection)
  (check-beta-bernoulli
   uncollapsed-beta-bernoulli-maker
   '((assume predictive (coin))
     (infer rdb-backpropagate-constraints!)
     (infer rejection)
     (predict predictive))))

(define-test (collapsed-beta-bernoulli)
  (check-beta-bernoulli
   collapsed-beta-bernoulli-maker
   '((infer rdb-backpropagate-constraints!)
     (infer enforce-constraints) ; Note: no mcmc
     ;; Predicting (coin) instead of (assume prediction (coin))
     ;; (infer...) (predict prediction) because
     ;; enforce-constraints respects the originally-sampled
     ;; values, and I want to emphasize that MCMC is not needed
     ;; for a collapsed model.
     (predict (coin)))))

(define-test (uncollapsed-beta-bernoulli-explicitly-assessable)
  (check-beta-bernoulli
   uncollapsed-assessable-beta-bernoulli-maker
   '((assume predictive (coin))
     ;; Works with and without propagating constraints
     ;; (infer rdb-backpropagate-constraints!)
     (infer (mcmc 20))
     (predict predictive))))

(define-test (uncollapsed-beta-bernoulli-explicitly-assessable-rejection)
  (check-beta-bernoulli
   uncollapsed-assessable-beta-bernoulli-maker
   '((assume predictive (coin))
     ;; Works with and without propagating constraints
     ;; (infer rdb-backpropagate-constraints!)
     (infer rejection)
     (predict predictive))))

(define-test (uncollapsed-beta-bernoulli-explicitly-assessable-rejection)
  (check-beta-bernoulli
   uncollapsed-assessable-beta-bernoulli-maker
   '((assume predictive (coin))
     ;; Works with and without propagating constraints
     ;; (infer rdb-backpropagate-constraints!)
     (infer rejection)
     (predict predictive))))

(define-test (collapsed-beta-bernoulli-explicit-assessor)
  (check-beta-bernoulli
   collapsed-assessable-beta-bernoulli-maker
   '((infer enforce-constraints) ; Note: no mcmc
     ;; Predicting (coin) instead of (assume prediction (coin))
     ;; (infer...) (predict prediction) because
     ;; enforce-constraints respects the originally-sampled
     ;; values, and I want to emphasize that MCMC is not needed
     ;; for a collapsed model.
     (predict (coin)))))

(define-test (collapsed-beta-bernoulli-mixes)
  (let ()
    (define program
      (standard-beta-bernoulli-test-program
       collapsed-beta-bernoulli-maker
       '((infer rdb-backpropagate-constraints!)
         (infer enforce-constraints)
         (assume x (coin))
         (let ((pre-inf (predict x)))
           (infer (mcmc 10)) ; 10 rather than 1 because of the constraint propagation and mcmc correction bug
           (cons pre-inf (predict x))))))
    (define answer
      (square-discrete standard-beta-bernoulli-posterior))
    (check (> (chi-sq-test (collect-samples program 200) answer)
              *p-value-tolerance*))))

(define-test (collapsed-beta-bernoulli-mixes-rejection)
  (let ()
    (define program
      (standard-beta-bernoulli-test-program
       collapsed-beta-bernoulli-maker
       '((infer rdb-backpropagate-constraints!)
         (infer enforce-constraints)
         (assume x (coin))
         (let ((pre-inf (predict x)))
           (infer rejection)
           (cons pre-inf (predict x))))))
    (define answer
      (square-discrete standard-beta-bernoulli-posterior))
    (check (> (chi-sq-test (collect-samples program 200) answer)
              *p-value-tolerance*))))

(define-test (assessable-collapsed-beta-bernoulli-mixes)
  (let ()
    (define program
      (standard-beta-bernoulli-test-program
       collapsed-assessable-beta-bernoulli-maker
       '((infer enforce-constraints)
         (assume x (coin))
         (let ((pre-inf (predict x)))
           (infer (mcmc 1))
           (cons pre-inf (predict x))))))
    (define answer
      (square-discrete standard-beta-bernoulli-posterior))
    (check (> (chi-sq-test (collect-samples program 200) answer)
              *p-value-tolerance*))))

(define-test (assessable-collapsed-beta-bernoulli-mixes-rejection)
  (let ()
    (define program
      (standard-beta-bernoulli-test-program
       collapsed-assessable-beta-bernoulli-maker
       '((infer enforce-constraints)
         (assume x (coin))
         (let ((pre-inf (predict x)))
           (infer rejection)
           (cons pre-inf (predict x))))))
    (define answer
      (square-discrete standard-beta-bernoulli-posterior))
    (check (> (chi-sq-test (collect-samples program 200) answer)
              *p-value-tolerance*))))

(define-test (assessable-coupled-beta-bernoulli-transition-operator)
  ;; The bug this test is checking for is that coupled assessment in
  ;; the old trace might mistakenly use the local state from the end
  ;; of the run, rather than from the point in the run at which
  ;; assessment is called.
  ;;
  ;; Note: PETs will produce a different valid proposal in this
  ;; situation.  To wit, since in PETs the local state is actually
  ;; exchangeable, it is valid to use the final state, except for
  ;; unincorporating the choice to be proposed and anything else in
  ;; the brush.  That state then gets used by both the proposal
  ;; distribution and the assessment.  RandomDB can't use that state
  ;; for the proposal distribution, so it must not use it for
  ;; assessment either.
  (let ()
    ;; An example sufficient to exhibit that problem is two flips of a
    ;; collapsed assessable beta bernoulli (two because one of them
    ;; will be chosen as the resimulation target).
    (define program
      `(begin
         ,map-defn
         ,mcmc-defn
         ,observe-defn
         (model-in (rdb-extend (get-current-trace))
           (assume make-u-bb ,collapsed-assessable-beta-bernoulli-maker)
           (assume coin (make-u-bb))
           (assume f1 (coin))
           (assume f2 (coin))
           (let ((initial (predict (cons f1 f2))))
             (infer (mcmc 1))
             ;; We want to check that the transition operator is right.
             (list initial (predict (cons f1 f2)))))))

    (define initial-dist
      '(((#t . #t) . 1/3) ((#f . #f) . 1/3) ((#t . #f) . 1/6) ((#f . #t) . 1/6)))

    ;; The correct transition operator
    (define (true-post-infer-dist init)
      (chain-with freqs-bind
        (prop-index <- '((0 . 1/2) (1 . 1/2)))
        (prop-value <- (if (= prop-index 0)
                           '((#t . 1/2) (#f . 1/2))
                           (if (car init)
                               '((#t . 2/3) (#f . 1/3))
                               '((#t . 1/3) (#f . 2/3)))))
        (accept-prob <= (if (= prop-index 1)
                            1 ;; Nothing more to condition on
                            (if (equal? prop-value (car init))
                                1 ;; No rejecting non-moves
                                (if (equal? prop-value (cdr init))
                                    1 ;; (min 1 2) b/c moving to favorable state
                                    1/2 ;; M-H ratio for the move to the unfavorable state
                                    ))))
        (accept <- `((#t . ,accept-prob) (#f . ,(- 1 accept-prob))))
        (freqs-return
         (if accept
             (if (= prop-index 0)
                 (cons prop-value (cdr init))
                 (cons (car init) prop-value))
             init))))
    (define answer
      (freqs-normalize
       (chain-with freqs-bind
         (init <- initial-dist)
         (post <- (true-post-infer-dist init))
         (freqs-return (list init post)))
       data<))
    #;
    (pp (cons 'true-transition-operator
              (map (lambda (item prob)
                     (cons item (* 72 3 prob)))
                   (map car answer)
                   (map cdr answer))))

    ;; The buggy transition operator
    (define (assess-bug-post-infer-dist init)
      (chain-with freqs-bind
        (prop-index <- '((0 . 1/2) (1 . 1/2)))
        (prop-value <- (if (= prop-index 0)
                           '((#t . 1/2) (#f . 1/2))
                           (if (car init)
                               '((#t . 2/3) (#f . 1/3))
                               '((#t . 1/3) (#f . 2/3)))))
        (assessment-weight <= (cond ((equal? init '(#t . #t)) 3/4)
                                    ((equal? init '(#t . #f)) 1/2)
                                    ((equal? init '(#f . #t)) 1/2)
                                    ((equal? init '(#f . #f)) 1/4)))
        ;; Note assessment against the full state generated by the
        ;; initial draw; the proper thing to assess against would have
        ;; been only the state computed up to the point at which this
        ;; choice is made.
        (assessor <= (lambda (v) (if v assessment-weight (- 1 assessment-weight))))
        (accept-prob <= (if (= prop-index 0)
                            ;; Will absorb the second flip.
                            (let ((prob-from-new-trace (if (equal? (cdr init) prop-value) 2/3 1/3)))
                              (min 1 (/ prob-from-new-trace (assessor (car init)))))
                            ;; Will absorb the first flip
                            (let ((prob-from-new-trace 1/2))
                              (min 1 (/ prob-from-new-trace (assessor (cdr init)))))))
        ; (_ <= (pp `(model ,init ,prop-index ,prop-value ,assessment-weight ,accept-prob)))
        (accept <- `((#t . ,accept-prob) (#f . ,(- 1 accept-prob))))
        (freqs-return
         (if accept
             (if (= prop-index 0)
                 (cons prop-value (cdr init))
                 (cons (car init) prop-value))
             init)))
    (define assess-bug-answer
      (freqs-normalize
       (chain-with freqs-bind
         (init <- initial-dist)
         (post <- (assess-bug-post-infer-dist init))
         (freqs-return (list init post)))
       data<))
    #;
    (pp (cons 'assess-bug-transition-operator
              (map (lambda (item prob)
                     (cons item (* 72 3 prob)))
                   (map car assess-bug-answer)
                   (map cdr assess-bug-answer))))

    ;; Actually generate samples from the program and check them
    (let* ((result (collect-samples program (* 72 3 10)))
           (vs-truth (chi-sq-test result answer))
           (vs-assess-bug (chi-sq-test result assess-bug-answer)))
      ;; System should approximate the true behavior
      (check (> vs-truth *p-value-tolerance*))
      ;; We want enough statistical strength to be confident that
      ;; system does not have the assess bug
      (check (< vs-assess-bug (* *p-value-tolerance* 0.1))))))
