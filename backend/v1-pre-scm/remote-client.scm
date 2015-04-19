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

;;; Venture remote evaluation client.

;;; Point it at a server or a load balancer.

(declare (usual-integrations))

(define (venture-remote-eval service program)
  ((call-with-local-tcp-stream-socket service
     (lambda (socket)
       (network-write socket 'CLIENT)
       (network-write socket `(EVAL ,program))
       (match (ignore-errors (lambda () (network-read socket)))
	 (`(OK ,result)                 (lambda () result))
	 ('(FAIL)                       (lambda () (error "Eval failed!")))
	 (`(FAIL ,(? string? message))  (lambda ()
					  (error "Eval failed:" message)))
	 (else                          (lambda () (network-error))))))))

(define (venture-remote-terminate service)
  (call-with-local-tcp-stream-socket service
    (lambda (socket)
      (network-write socket 'TERMINATE))))

(define (venture-remote-eval* service programs)
  (let ((n (length programs))
	(lock (make-thread-mutex))
	(condvar (make-condition-variable "venture-eval")))
    (let ((errors '())
	  (results (make-vector n)))
      (do ((i 0 (+ i 1))
	   (programs programs (cdr programs)))
	  ((not (pair? programs)))
	(assert (< i n))
	(let ((program (car programs)))
	  (spawn-thread
	    (lambda ()
	      (define (finish error? result)
		(with-thread-mutex-locked lock
		  (lambda ()
		    (if error? (set! errors (cons i errors)))
		    (vector-set! results i result)
		    (assert (< 0 n))
		    (set! n (- n 1))
		    (condition-variable-signal! condvar)))
		(exit-current-thread 0))
	      (finish
	       #f
	       (bind-condition-handler (list condition-type:error)
		   (lambda (condition)
		     (finish #t condition))
		 (lambda ()
		   (venture-remote-eval service program))))))))
      (with-thread-mutex-locked lock
	(lambda ()
	  (do () ((zero? n))
	    (condition-variable-wait! condvar lock))))
      (if (pair? errors)
	  (error "Remote evaluation errors:"
		 (map (lambda (i) (vector-ref results i))
		      (sort errors <)))
	  (vector->list results)))))
