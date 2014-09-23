(declare (usual-integrations))

;;; From http://en.wikipedia.org/wiki/Kolmogorov-Smirnov_test

(define (k-s-cdf-series-one-term x k)
  (* (expt -1 (- k 1))
     (exp (* -2 k k x x))))

(define (sum-series term)
  (let loop ((next-k 1)
             (total 0))
    (let ((next-term (term next-k)))
      (if (< (abs (* next-term 1e14)) (abs total))
          (+ total next-term)
          (loop (+ next-k 1)
                (+ total next-term))))))

(define (k-s-cdf-by-series-one x)
  (sum-series (lambda (k) (k-s-cdf-series-one-term x k))))

(define (kolmogorov-survivor-function-by-series-one x)
  (* 2 (k-s-cdf-by-series-one x)))

(define (k-s-D-stat data cdf)
  (let* ((data (sort data <))
         (n (length data))
         (cdfvals (map cdf data))
         (D+ ((access apply system-global-environment)
              max (map (lambda (i cdfval)
                         (- (/ (+ i 1) n) cdfval))
                       (iota n) cdfvals)))
         (D- ((access apply system-global-environment)
              min (map (lambda (i cdfval)
                         (- (/ i n) cdfval))
                       (iota n) cdfvals))))
    (max (abs D+) (abs D-))))

(define (k-s-test data cdf)
  (let ((n (length data))
        (D-stat (k-s-D-stat data cdf)))
    (list D-stat (kolmogorov-survivor-function-by-series-one (* D-stat (sqrt n))))))

#|

 (define (uniform-cdf low high)
   (lambda (place)
     (min 1
          (max 0
               (/ (- place low)
                  (- high low))))))

1 ]=> (k-s-test '(.1 .1 .2) (uniform-cdf 0 1))

;Value 20: (.8 4.2986775848567596e-2)

1 ]=> (k-s-test '(.1 .1 .2 .3) (uniform-cdf 0 1))

;Value 21: (.7 3.9681879538114403e-2)

1 ]=> (k-s-test '(.1 .2 .3) (uniform-cdf 0 1))

;Value 22: (.7 .10571583583368427)

1 ]=> (k-s-test '(.1 .2 .3 .9) (uniform-cdf 0 1))

;Value 23: (.45 .39273070794065434)

1 ]=> (k-s-test '(.1 .2 .3 .8 .9) (uniform-cdf 0 1))

;Value 24: (.3 .7590978384203949)

1 ]=> (k-s-test '(.1 .2 .3 .8 .9 .1 .2 .3 .8 .9) (uniform-cdf 0 1))

;Value 25: (.3 .32910478909781504)

1 ]=> (k-s-test '(.1 .2 .3 .8 .9 .1 .2 .3 .8 .9 .1 .2 .3 .8 .9) (uniform-cdf 0 1))

;Value 26: (.3 .13437022652861091)

1 ]=> (k-s-test '(.1 .2 .3 .8 .9 .1 .2 .3 .8 .9 .1 .2 .3 .8) (uniform-cdf 0 1))

;Value 27: (.3428571428571429 .07439750491383416)

1 ]=> 
|#
