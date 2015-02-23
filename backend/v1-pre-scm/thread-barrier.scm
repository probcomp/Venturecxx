;;; -*- Mode: Scheme -*-

;;; Copyright (c) 2014, Taylor R. Campbell.
;;;
;;; This program is free software: you can redistribute it and/or
;;; modify it under the terms of the GNU General Public License as
;;; published by the Free Software Foundation, either version 3 of the
;;; License, or (at your option) any later version.
;;;
;;; This program is distributed in the hope that it will be useful, but
;;; WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;;; General Public License for more details.
;;;
;;; You should have received a copy of the GNU General Public License
;;; along with this program.  If not, see
;;; <http://www.gnu.org/licenses/>.

(declare (usual-integrations))

(define-structure (thread-barrier
		   (constructor %make-thread-barrier (count current))
		   (conc-name thread-barrier.))
  (lock (make-thread-mutex) read-only #t)
  (condvar (make-condition-variable) read-only #t)
  (count #f read-only #t)
  current
  (generation 0))

(define-guarantee thread-barrier "thread barrier")

(define (make-thread-barrier count)
  (guarantee-exact-positive-integer count 'MAKE-THREAD-BARRIER)
  (%make-thread-barrier count count))

(define (thread-barrier-wait barrier)
  (guarantee-thread-barrier barrier 'THREAD-BARRIER-WAIT)
  (let ((lock (thread-barrier.lock barrier))
	(condvar (thread-barrier.condvar barrier)))
    (with-thread-mutex-locked lock
      (lambda ()
	(let ((count (thread-barrier.count barrier))
	      (current (thread-barrier.current barrier))
	      (generation (thread-barrier.generation barrier)))
	  (assert (< 0 current))
	  (assert (<= current count))
	  (let ((next (- current 1)))
	    (if (zero? next)
		(begin
		  (set-thread-barrier.current! barrier count)
		  (set-thread-barrier.generation! barrier (+ 1 generation))
		  (condition-variable-broadcast! condvar)
		  #t)
		(begin
		  (set-thread-barrier.current! barrier next)
		  (do () ((< generation (thread-barrier.generation barrier)))
		    (condition-variable-wait! condvar lock))
		  #f))))))))
