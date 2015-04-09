;;; Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

(define-structure (address
                   (constructor %make-address)
                   (print-procedure
                    (simple-unparser-method 'A (lambda (address) (list (address-index address))))))
  index)

(define-integrable (address<? a1 a2)
  (fix:< (address-index a1) (address-index a2)))

(define address-wt-tree-type (make-wt-tree-type address<?))
