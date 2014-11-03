(in-test-group
 show-off

 (define-test (generate-gamma)
   (define program
     `(begin
        ,observe-defn
        (define gamma-base
          (lambda (alpha)
            (model-in (rdb-extend (get-current-trace))
              (assume V (uniform 0 1))
              (assume X (expt V (/ 1 alpha)))
              (observe (flip (exp (- X))) #t)
              (infer rejection)
              (predict X))))
        (define gamma
          (lambda (alpha beta)
            (/ (gamma-base alpha) beta)))
        (gamma 2 1)))
   (check (> (k-s-test (collect-samples program)
                       (gamma-cdf 2 1))
             *p-value-tolerance*))))
