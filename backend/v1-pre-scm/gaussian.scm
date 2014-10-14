(declare (usual-integrations))

(define gaussian-defn
  `(begin
     (define box-muller-xform
       (lambda (u1 u2)
         (* (sqrt (* -2 (log u1)))
            (cos (* 2 3.1415926535897932846 u2)))))
     (define simulate-normal
       (lambda (mu sig)
         (+ mu (* sig (box-muller-xform (uniform 0 1) (uniform 0 1))))))
     (define normal-log-density
       (lambda (x mu sig)
         (- (/ (* -1 (expt (- x mu) 2))
               (* 2 (expt sig 2)))
            (+ (log sig)
               (* 1/2 (+ (log 2) (log 3.1415926535897932846)))))))
     (define normal (make-sp simulate-normal normal-log-density))))

(define gaussian-by-inference-defn
  `(begin
     ,gaussian-defn
     ,map-defn
     ,mcmc-defn
     ,observe-defn
     (define my-normal
       (make-sp
        (lambda (mu sig)
          (model-in (rdb-extend (get-current-trace))
            (assume x (normal 0 (* (sqrt 2) sig)))
            ;; TODO Do I need to compute the observation mean in the external trace?
            ;; How?  Let-bind?  Introduce an unquote for model-in?  Tweak observe?
            (observe (normal x (* (sqrt 2) sig)) (* 2 mu))
            (infer (mcmc 10))
            (predict x)))
        normal-log-density))))

(define (gaussian-example iterations)
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     ,gaussian-defn
     (model-in (rdb-extend (get-current-trace))
       (assume mu (normal 0 1))
       (observe (normal mu 1) 2)
       ,@(if (= 0 iterations)
             '()
             `((infer (mcmc ,iterations))))
       (predict mu))))

(define gaussian-example-prior-cdf
  (lambda (x) (gaussian-cdf x 0 1)))

(define gaussian-example-posterior-cdf
  (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2)))))

(define (gaussian-example-plots iter-counts)
  (let* ((sample-sets (map collect-samples (map gaussian-example iter-counts)))
         (bounds (lset-union (car sample-sets) (last sample-sets))))
    (gnuplot-multiple
     `(,(gnuplot-function-plot-near
         gaussian-example-prior-cdf bounds '(commanding "title \"analytic prior CDF\""))
       ,@(map (lambda (samples i)
                (gnuplot-empirical-cdf-plot samples (string-append "after " (number->string i) " iterations")))
              sample-sets iter-counts)
       ,(gnuplot-function-plot-near
         gaussian-example-posterior-cdf bounds '(commanding "title \"analytic posterior CDF\""))))))
