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

;;; Some utilities for computing exact answers to questions about
;;; small, discrete probability distributions.

;;; TODO Canonicalize to wt-tree representation of distributions?
;;; (will improve asymptotics of chi-sq test)

(define (discrete-iid-map f d1 d2)
  (append-map (lambda (p1)
                (map (lambda (p2)
                       (cons (f (car p1) (car p2))
                             (* (cdr p1) (cdr p2))))
                     d2))
              d1))
(define (square-discrete d) (discrete-iid-map cons d d))

(define (freqs-return datum)
  `((,datum . 1)))

(define (freqs-bind d f)
  (define (possible? pair)
    (let ((prob (cdr pair)))
      (not (and (exact? prob)
                (= 0 prob)))))
  (append-map
   (lambda (p1)
     (let ((item (car p1))
           (prob (cdr p1)))
       (map (lambda (p2)
              (let ((item* (car p2))
                    (prob* (cdr p2)))
                (cons item* (* prob prob*))))
            (f item))))
   (filter possible? d)))

(define (freqs-normalize d <)
  (wt-tree->alist
   (fold (lambda (item prob tree)
           (wt-tree/add tree item (+ prob (wt-tree/lookup tree item 0))))
         (make-wt-tree (make-wt-tree-type <))
         (map car d)
         (map cdr d))))
