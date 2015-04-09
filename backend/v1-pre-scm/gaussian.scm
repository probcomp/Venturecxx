;;; Copyright (c) 2014 MIT Probabilistic Computing Project.
;;;
;;; This file is part of Venture.
;;;
;;; Venture is free software: you can redistribute it and/or modify
;;; it under the terms of the GNU General Public License as published by
;;; the Free Software Foundation, either version 3 of the License, or
;;; (at your option) any later version.
;;;
;;; Venture is distributed in the hope that it will be useful,
;;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;;; GNU General Public License for more details.
;;;
;;; You should have received a copy of the GNU General Public License
;;; along with Venture.  If not, see <http://www.gnu.org/licenses/>.

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
            ;; The (* 2 mu) expression is computed in the model trace,
            ;; and its value is recorded as the desired constraint.
            ;; In this case, this is OK, because said value is constant.
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
