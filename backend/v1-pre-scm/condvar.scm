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

(define-structure (condition-variable
                   (conc-name condition-variable.)
                   (constructor %make-condition-variable
                                (name waiter-head waiter-tail)))
  (name #f read-only #t)
  (waiter-head #f read-only #t)
  (waiter-tail #f read-only #t)
  (specific unspecific)
  (thread-mutex (make-thread-mutex) read-only #t))

(define-guarantee condition-variable "condition variable")
(define-guarantee thread-mutex "thread mutex") ;XXX !@*#&@!

(define (make-condition-variable #!optional name)
  (let ((name (if (default-object? name) unspecific name))
        (waiter-head (make-waiter #f))
        (waiter-tail (make-waiter #f)))
    (set-waiter.next! waiter-head waiter-tail)
    (set-waiter.previous! waiter-tail waiter-head)
    (%make-condition-variable name waiter-head waiter-tail)))

(define (with-condition-variable-locked condvar procedure)
  (assert (condition-variable? condvar))
  (guarantee-procedure-of-arity procedure 0 'WITH-CONDITION-VARIABLE-LOCKED)
  (assert (not (condition-variable-locked? condvar)))
  (let ((thread-mutex (condition-variable.thread-mutex condvar)))
    (dynamic-wind (let ((done? #f))
                    (lambda ()
                      (if done? (error "Re-entry prohibited!"))
                      (set! done? #t)
                      (lock-thread-mutex thread-mutex)))
                  procedure
                  (lambda () (unlock-thread-mutex thread-mutex)))))

(define (condition-variable-locked? condvar)
  (eq? (current-thread)
       (thread-mutex-owner (condition-variable.thread-mutex condvar))))

(define (condition-variable-name condvar)
  (guarantee-condition-variable condvar 'CONDITION-VARIABLE-NAME)
  (condition-variable.name condvar))

(define (condition-variable-specific condvar)
  (guarantee-condition-variable condvar 'CONDITION-VARIABLE-SPECIFIC)
  (condition-variable.specific condvar))

(define (condition-variable-specific-set! condvar specific)
  (guarantee-condition-variable condvar 'SET-CONDITION-VARIABLE-SPECIFIC!)
  (set-condition-variable.specific! condvar specific))

(define (unlock-thread-mutex-and-wait thread-mutex condvar #!optional timeout)
  (guarantee-condition-variable condvar 'CONDITION-VARIABLE-WAIT!/UNLOCK)
  (guarantee-thread-mutex thread-mutex 'CONDITION-VARIABLE-WAIT!/UNLOCK)
  (%condition-variable-wait!/unlock condvar thread-mutex timeout))

(define (condition-variable-wait! condvar thread-mutex #!optional timeout)
  (guarantee-condition-variable condvar 'CONDITION-VARIABLE-WAIT!)
  (guarantee-thread-mutex thread-mutex 'CONDITION-VARIABLE-WAIT!)
  (begin0 (%condition-variable-wait!/unlock condvar thread-mutex timeout)
    (lock-thread-mutex thread-mutex)))

(define (%condition-variable-wait!/unlock condvar thread-mutex timeout)
  (let ((waiter (make-waiter (current-thread))))
    (define (with-lock body) (with-condition-variable-locked condvar body))
    (let ((blocked? (block-thread-events)))
      (with-lock (lambda () (enqueue-waiter! condvar waiter)))
      (unlock-thread-mutex thread-mutex)
      (begin0
          (let loop ()
            (cond ((and (real? timeout) (<= (real-time-clock) timeout)) #f)
                  ((waiter.done? waiter) #t)
                  (else (suspend-current-thread) (loop))))
        (with-lock
          (lambda ()
            ;; Signaller got interrupted or we timed out.  Clean up.
            (if (not (waiter-detached? condvar waiter))
                (remove-waiter! condvar waiter))))
        (if (not blocked?)
            (unblock-thread-events))))))

(define (condition-variable-signal! condvar)
  (guarantee-condition-variable condvar 'CONDITION-VARIABLE-SIGNAL!)
  (with-condition-variable-locked condvar
    (lambda ()
      (let ((head (condition-variable.waiter-head condvar))
            (tail (condition-variable.waiter-tail condvar)))
        (assert (waiter? head))
        (assert (waiter? tail))
        (assert (not (eq? head tail)))
        (let loop ((waiter (waiter.next head)))
          (assert (waiter? waiter))
          (if (not (eq? waiter tail))
              (if (waiter.done? waiter)
                  (let ((next (waiter.next waiter)))
                    ;; Must've been interrupted, but it's done anyway,
                    ;; so skip it.
                    (remove-waiter! condvar waiter)
                    (loop next))
                  ;; Order of modifications matters for robustness
                  ;; against interruption.  If we mark it done before
                  ;; we've scheduled a wakeup, the thread may never
                  ;; be woken.  If we remove it from the queue before
                  ;; marking it done, it may never be marked done and
                  ;; the thread may awaken but go right back to sleep
                  ;; forever because it appears unready.
                  (begin (signal-thread-event (waiter.thread waiter) #f)
                         (set-waiter.done?! waiter #t)
                         (remove-waiter! condvar waiter)
                         unspecific)))))))
  unspecific)

(define (condition-variable-broadcast! condvar)
  (guarantee-condition-variable condvar 'CONDITION-VARIABLE-BROADCAST!)
  (with-condition-variable-locked condvar
    (lambda ()
      (let ((head (condition-variable.waiter-head condvar))
            (tail (condition-variable.waiter-tail condvar)))
        (assert (waiter? head))
        (assert (waiter? tail))
        (assert (not (eq? head tail)))
        (let loop ((waiter (waiter.next head)))
          (assert (waiter? waiter))
          (if (not (eq? waiter tail))
              (let ((next (waiter.next waiter)))
                (if (not (waiter.done? waiter))
                    (begin (signal-thread-event (waiter.thread waiter) #f)
                           (set-waiter.done?! waiter #t)))
                (remove-waiter! condvar waiter)
                (loop next)))))))
  unspecific)

(define-structure (waiter
                   (conc-name waiter.)
                   (constructor make-waiter (thread)))
  (thread #f read-only #t)
  (done? #f)
  (previous #f)
  (next #f))

(define (waiter-detached? condvar waiter)
  (assert (condition-variable? condvar))
  (assert (condition-variable-locked? condvar))
  (not (or (waiter.previous waiter)
           (waiter.next waiter))))

(define (enqueue-waiter! condvar waiter)
  (assert (condition-variable? condvar))
  (assert (condition-variable-locked? condvar))
  (assert (waiter? waiter))
  (assert (not (waiter.previous waiter)))
  (assert (not (waiter.next waiter)))
  (let ((tail (condition-variable.waiter-tail condvar)))
    (assert (waiter? tail))
    (assert (not (waiter.next tail)))
    (let ((previous (waiter.previous tail)))
      (assert (waiter? previous))
      (assert (not (eq? tail previous)))
      (assert (eq? tail (waiter.next previous)))
      ;; Commit the changes all together or not at all.
      (without-interrupts
       (lambda ()
         (set-waiter.previous! tail waiter)
         (set-waiter.next! previous waiter)
         (set-waiter.previous! waiter previous)
         (set-waiter.next! waiter tail))))))

(define (remove-waiter! condvar waiter)
  (assert (condition-variable? condvar))
  (assert (condition-variable-locked? condvar))
  (assert (waiter? waiter))
  (let ((previous (waiter.previous waiter))
        (next (waiter.next waiter)))
    (assert (waiter? previous))
    (assert (waiter? next))
    (assert (not (eq? waiter previous)))
    (assert (not (eq? waiter next)))
    (assert (eq? waiter (waiter.next previous)))
    (assert (eq? waiter (waiter.previous next)))
    ;; Commit the changes all together or not at all.
    (without-interrupts
     (lambda ()
       (set-waiter.next! previous next)
       (set-waiter.previous! next previous)
       (set-waiter.next! waiter #f)
       (set-waiter.previous! waiter #f)))))
