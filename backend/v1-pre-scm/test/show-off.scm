(in-test-group
 show-off

 (define-test (generate-truncated-gamma)
   (define program
     `(begin
        ,observe-defn
        (define standard-truncated-gamma
          (lambda (alpha)
            (model-in (rdb-extend (get-current-trace))
              (assume V (uniform 0 1))
              (assume X (expt V (/ 1 alpha)))
              (observe (flip (exp (- X))) #t)
              (infer rejection)
              (predict X))))
        (define truncated-gamma
          (lambda (alpha beta)
            (/ (standard-truncated-gamma alpha) beta)))
        (truncated-gamma 2 1)))
   (check (> (k-s-test (collect-samples program)
                       (lambda (x)
                         (/ ((gamma-cdf 2 1) x) ((gamma-cdf 2 1) 1))))
             *p-value-tolerance*)))

 (define-test (marsaglia-tsang-gamma)
   (define (program shape)
     `(begin
        ,exactly-defn
        ,observe-defn
        ,gaussian-defn
        (define marsaglia-standard-gamma-for-shape>1
          (lambda (alpha)
            (let ((d (- alpha 1/3)))
              (let ((c (/ 1 (sqrt (* 9 d)))))
                (model-in (rdb-extend (get-current-trace))
                  (assume x (normal 0 1))
                  (assume v (expt (+ 1 (* c x)) 3))
                  (observe (exactly (> v 0)) #t)
                  ;; Unless I use a short-circuit and between these
                  ;; two tests, this reject step is necessary to
                  ;; ensure that the next observation will not crash
                  ;; when forward-simulating for the first time.
                  (infer rejection)
                  (observe (exactly (< (log (uniform 0 1)) (+ (* 0.5 x x) (* d (+ 1 (- v) (log v)))))) #t)
                  (infer rejection)
                  (predict (* d v)))))))
        (marsaglia-standard-gamma-for-shape>1 ,shape)))
   (check (> (k-s-test (collect-samples (program 2)) (gamma-cdf 2 1))
             *p-value-tolerance*)))

 (define-test (gamma-assess)
   (define (assess-gamma x alpha beta)
     (+ (* alpha (log beta))
        (* (- alpha 1) (log x))
        (* -1 beta x)
        (* -1 (log-gamma alpha))))
   (for-each (lambda (x)
               (check (< (abs (- (/ (exp (assess-gamma x 1.2 2))
                                    ((gamma-pdf 1.2 2) x))
                                 1))
                         1e-10)))
             (map (lambda (x) (* 0.3 x)) (cdr (iota 100)))))

 (define-test (add-data-and-predict)
   (define program
     `(begin
        ,observe-defn
        ,map-defn
        ,mcmc-defn
        (model-in (rdb-extend (get-current-trace))
          (assume is-trick? (flip 0.1))
          (assume weight (if is-trick? (uniform 0 1) 0.5))
          (define add-data-and-infer
            (lambda ()
              ;; The trace in which this observe is run is
              ;; dynamically scoped right now
              (observe (flip weight) #t)
              (infer (mcmc 10))))
          (define find-trick
            (lambda ()
              (if (not (predict is-trick?))
                  (begin
                    (add-data-and-infer)
                    (find-trick))
                  'ok)))
          (find-trick)
          (predict weight))))
   ;; Check that it runs, but I have no idea what the distribution on
   ;; weights should be.
   (top-eval program)))
