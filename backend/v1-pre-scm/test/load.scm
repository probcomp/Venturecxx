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

(define (self-relatively thunk)
  (if (current-eval-unit #f)
      (with-working-directory-pathname
       (directory-namestring (current-load-pathname))
       thunk)
      (thunk)))

(define (load-relative filename #!optional environment)
  (self-relatively (lambda () (load filename environment))))

(define test-environment (make-top-level-environment))

(load-relative "../testing/load" test-environment)

(let ((client-environment (the-environment)))
  (for-each
   (lambda (n)
     (environment-link-name client-environment test-environment n))
   '( define-each-check
      define-test
      in-test-group
      *current-test-group* ; pulled in by macro
      tg:find-or-make-subgroup ; pulled in by macro
      check
      register-test
      make-single-test
      detect-docstring
      generate-test-name
      better-message
      assert-proc
      run-tests-and-exit
      run-registered-tests
      run-test
      assert-true)))

(load-relative "stats")

(define *num-samples* 50)

(define (collect-samples prog #!optional count)
  (map (lambda (i)
         ; (pp `(running ,i))
         (top-eval prog))
       (iota (if (default-object? count) *num-samples* count))))

(define *p-value-tolerance* 0.01)

(load-relative "sanity")
(load-relative "discrete")
(load-relative "continuous")
(load-relative "overincorporation")
(load-relative "show-off")
