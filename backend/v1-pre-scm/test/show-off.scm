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
             *p-value-tolerance*))))
