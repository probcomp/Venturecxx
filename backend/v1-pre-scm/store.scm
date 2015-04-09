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

;;; A minimal "trace" that just stores the values and does not allow
;;; re-execution.

(define-structure (store (safe-accessors #t))
  parent
  values ; wt-tree mapping addresses to values
  )

;; TODO Make parent fetching generic, and implement trace-search
;; uniformly over all trace types
(define (store-trace-search trace addr win lose)
  (if (store? trace)
      (store-trace-search-one trace addr win
       (lambda () (trace-search (store-parent trace) addr win lose)))
      (lose)))

(define (store-trace-search-one trace addr win lose)
  (search-wt-tree (store-values trace) addr win lose))

(define (store-trace-eval! trace exp env addr read-traces continue)
  (let ((answer (continue)))
    (set-store-values! trace (wt-tree/add (store-values trace) addr answer))
    answer))

(define (store-trace-apply! trace oper opand-addrs addr read-traces continue)
  (continue))

(define (store-record-constraint! trace addr value)
  (error "Forward execution does not support constraining; did you mean to use mutation?" trace addr value))

(define (store-extend trace)
  (make-store trace (make-address-wt-tree)))
