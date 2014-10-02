(define two-coin-flipping-example
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.5))
       (assume c2 (flip 0.5))
       (observe (flip (if (boolean/or c1 c2) 1 0.0001)) #t)
       (infer (mcmc 20))
       (predict c1))))

(define-test (two-coin-dist)
  (let ()
    (check (> (chi-sq-test (collect-samples two-coin-flipping-example)
                           '((#t . 2/3) (#f . 1/3))) 0.001))))

(define two-coins-with-brush-example
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.5))
       (assume c2 (if c1 #t (flip 0.5)))
       (observe (flip (if (boolean/or c1 c2) 1 0.0001)) #t)
       (infer (mcmc 20))
       (predict c1))))

(define-test (two-coin-brush-dist)
  (let ()
    (check (> (chi-sq-test (collect-samples two-coins-with-brush-example)
                           '((#t . 2/3) (#f . 1/3))) 0.001))))

(define two-mu-coins-with-brush-example
  `(begin
     ,observe-defn
     ,mu-flip-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (mu-flip 0.5))
       (assume c2 (if c1 #t (mu-flip 0.5)))
       (observe (mu-flip (if (boolean/or c1 c2) 1 0.0001)) #t)
       (infer (mcmc 20))
       (predict c1))))

(define-test (two-mu-coin-brush-dist)
  (let ()
    (check (> (chi-sq-test (collect-samples two-mu-coins-with-brush-example)
                           '((#t . 2/3) (#f . 1/3))) 0.001))))
