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

;;; Trivial single-threaded server.  Not useful for parallelization.
;;; Useful perhaps for testing.

(declare (usual-integrations))

(define (run-venture-server service when-ready)
  (call-with-local-tcp-server-socket service
    (lambda (server-socket)
      (when-ready service)
      (let loop ()
	((call-with-accept-socket server-socket
	   (lambda (socket)
	     (let ((id (ignore-errors (lambda () (network-read socket)))))
	       (case id
		 ((CLIENT)
		  (match (ignore-errors (lambda () (network-read socket)))
		    (`(EVAL ,program)
		     ((lambda (result)
			(ignore-errors
			 (lambda () (network-write socket result))))
		      (call-with-current-continuation
		       (lambda (return)
			 (bind-condition-handler (list condition-type:error)
			     (lambda (condition)
			       (return
				(ignore-errors
				 (lambda ()
				   `(FAIL ,(condition->string condition)))
				 (lambda (condition*) condition* '(FAIL)))))
			   (lambda ()
			     `(OK ,(top-eval program)))))))))
		  loop)
		 ((TERMINATE) (lambda () 0))
		 (else loop))))))))))