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

;;; Procedures

;; Tag for annotating procedures with assessors.
(define assessor-tag (make-annotation-tag))

;; Assessors are so common that I abstract tagging with them.
(define (make-sp simulator assessor)
  (annotate simulator assessor-tag assessor))
(define-integrable has-assessor? (has-annotation? assessor-tag))
(define-integrable assessor-of (annotation-of assessor-tag))

;; Tag for annotating procedures with ordered outputs with metadata
;; indicating upper bounds.  Annotating assessors with this is used to
;; compute the bound for rejection sampling.
(define value-bound-tag (make-annotation-tag))

(define flip
  (make-sp
   (scheme-procedure-over-values->v1-foreign
    (lambda (#!optional weight)
      (< (random 1.0)
         (if (default-object? weight)
             0.5
             weight))))
   (annotate
    (scheme-procedure-over-values->v1-foreign
     (lambda (val #!optional weight)
       (log (if (default-object? weight)
                0.5
                (if val weight (- 1 weight))))))
    value-bound-tag
    (scheme-procedure-over-values->v1-foreign
     (lambda (val #!optional weight)
       (if (default-object? weight)
           (log 0.5)
           0))))))

(define uniform
  (make-sp
   (scheme-procedure-over-values->v1-foreign
    (lambda (low high)
      (+ low (random (exact->inexact (- high low))))))
   (scheme-procedure-over-values->v1-foreign
    (lambda (val low high)
      (if (< low val high)
          (- (log (- high low)))
          minus-inf)))))

(define observe-defn
  '(define $observe
     (lambda (found desired)
       (begin
         (define t (get-current-trace))
         (define e (get-current-environment))
         (define addr (env-lookup e 'found))
         ;; When inference reruns the program, it will re-record the
         ;; constraint.  That might be fine.
         (record-constraint! t addr desired)))))

(define map-defn
  '(define map
     (lambda (f lst)
       (if (pair? lst)
           (cons (f (car lst)) (map f (cdr lst)))
           lst))))

;; The deterministic identity function, cast as assessable.  Useful
;; for rejection sampling with discrete observations.
(define exactly-defn
  '(define exactly
     (make-sp
      (lambda (x) x)
      (annotate
       (lambda (val x)
         (if (equal? val x)
             0
             minus-inf))
       value-bound-tag
       (lambda (val x) 0)))))

(define mu-flip-defn
  `(begin
     (define simulate-flip
       (lambda (weight)
         (< (random 1.0) weight)))
     (define flip-log-density
       (lambda (b weight)
         (log (if b weight (- 1 weight)))))
     (define flip-log-density-bound
       (lambda (b weight) 0))
     (define mu-flip
       (make-sp simulate-flip (annotate flip-log-density value-bound-tag flip-log-density-bound)))))

(define prim-map
  (scheme-procedure-over-values->v1-foreign
   (lambda (f lst)
     (let loop ((lst lst)
                (results '()))
       (if (pair? lst)
           (make-evaluation-request
            `((quote ,f) (quote ,(car lst)))
            #f
            (scheme-procedure-over-values->v1-foreign
             (lambda (res)
               (loop (cdr lst) (cons res results)))))
           (reverse results))))))
