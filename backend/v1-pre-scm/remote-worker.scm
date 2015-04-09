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

;;; Venture remote evaluation load balancer worker.

(declare (usual-integrations))

(define (run-venture-worker service when-ready)
  (call-with-local-tcp-stream-socket service
    (lambda (socket)
      (when-ready)
      ;; This is worker, hello!
      (network-write socket 'WORKER)
      (let loop ()
	(match (network-read socket)
	  (`(EVAL ,program)
	   (network-write
	    socket
	    (call-with-current-continuation
	     (lambda (return)
	       (bind-condition-handler (list condition-type:error)
		   (lambda (condition)
		     (return
		      (ignore-errors
		       (lambda () `(FAIL ,(condition->string condition)))
		       (lambda (condition*) condition* '(FAIL)))))
		 (lambda ()
		   `(OK ,(top-eval program)))))))
	   (loop))
	  (else 0))))))