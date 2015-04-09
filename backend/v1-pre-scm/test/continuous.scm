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

(define-test (forward-normal-dist)
  (let ()
    (define samples (collect-samples `(begin ,gaussian-defn (normal 0 1))))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 0 1))) *p-value-tolerance*))))

(define-test (forward-2-normal-dist)
  (let ()
    (define samples
      (collect-samples
       `(begin
          ,gaussian-defn
          (normal (normal 0 1) 1))))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 0 (sqrt 2)))) *p-value-tolerance*))))

(define-test (unrestricted-infer-normal-dist)
  (let ()
    (define samples
      (collect-samples
       `(begin
          ,map-defn
          ,mcmc-defn
          ,gaussian-defn
          (model-in (rdb-extend (get-current-trace))
            (assume mu (normal 0 1))
            (assume y (normal mu 1))
            (infer (mcmc 10))
            (predict mu)))))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 0 1))) *p-value-tolerance*))))

(define-test (observed-normal-dist)
  (let ()
    (define samples (collect-samples (gaussian-example 20)))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2))))) *p-value-tolerance*))))

(define-test (observing-begin-form)
  (let ()
    (define program
      `(begin
         ,map-defn
         ,mcmc-defn
         ,observe-defn
         ,gaussian-defn
         (model-in (rdb-extend (get-current-trace))
           (assume my-normal (lambda (mu sig) (normal mu sig)))
           (assume x (my-normal 0 1))
           (observe (begin (normal x 1)) 2)
           (infer rdb-backpropagate-constraints!)
           (infer (mcmc 10))
           (predict x))))
    (define samples (collect-samples program))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2))))) *p-value-tolerance*))))

(define-test (observing-compound-application)
  (let ()
    (define program
      `(begin
         ,map-defn
         ,mcmc-defn
         ,observe-defn
         ,gaussian-defn
         (model-in (rdb-extend (get-current-trace))
           (assume my-normal (lambda (mu sig) (normal mu sig)))
           (assume x (my-normal 0 1))
           (observe (my-normal x 1) 2)
           (infer rdb-backpropagate-constraints!)
           (infer (mcmc 10))
           (predict x))))
    (define samples (collect-samples program))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2))))) *p-value-tolerance*))))

(define-test (observing-variable-lookup)
  (let ()
    (define program
      `(begin
         ,map-defn
         ,mcmc-defn
         ,observe-defn
         ,gaussian-defn
         (model-in (rdb-extend (get-current-trace))
           (assume x (normal 0 1))
           (assume y (normal x 1))
           (observe y 2)
           (infer rdb-backpropagate-constraints!)
           (infer (mcmc 10))
           (predict x))))
    (define samples (collect-samples program))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2))))) *p-value-tolerance*))))

(define-test (modelling-by-inference-smoke)
  (check (> (k-s-test (collect-samples `(begin ,gaussian-by-inference-defn (my-normal 0 1)))
                      (lambda (x) (gaussian-cdf x 0 1)))
            *p-value-tolerance*)))
#;
(define-test (modelling-by-inference)
  (check (> (k-s-test (collect-samples `(begin
                                          ,gaussian-by-inference-defn
                                          (model-in (rdb-extend (get-current-trace))
                                            (assume x (my-normal 0 1))
                                            (observe (my-normal x 1) 2)
                                            (infer (mcmc 20))
                                            (predict x))))
                      (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2)))))
            *p-value-tolerance*)))
