;;; Venture remote evaluation client.

;;; Point it at a server or a load balancer.

(declare (usual-integrations))

(define (venture-remote-eval host service program)
  ((call-with-tcp-stream-socket host service
     (lambda (socket)
       (network-write socket 'CLIENT)
       (network-write socket `(EVAL ,program))
       (match (network-read socket)
	 (`(OK ,result)                 (lambda () result))
	 (`(FAIL ,(? string? message))  (lambda ()
					  (error "Eval failed:" message)))
	 (else                          (lambda () (network-error))))))))

(define (venture-remote-terminate host service)
  (call-with-tcp-stream-socket host service
    (lambda (socket)
      (network-write socket 'TERMINATE))))

(define (venture-remote-eval* host service programs)
  (let ((n (length programs))
	(lock (make-thread-mutex))
	(condvar (make-condition-variable "venture-eval"))
	(thread (current-thread)))
    (let ((results (make-vector n)))
      (do ((i 0 (+ i 1))
	   (programs programs (cdr programs)))
	  ((not (pair? programs)))
	(assert (< i n))
	(let ((program (car programs)))
	  (create-thread #f
	    (lambda ()
	      (bind-condition-handler (list condition-type:error)
		  (lambda (condition)
		    (signal-thread-event
		     thread
		     (lambda ()
		       ;; XXX Cancel other evaluation requests.
		       (error "Evaluation failed:" program condition)))
		    (exit-current-thread 0))
		(lambda ()
		  (let ((result (venture-remote-eval host service program)))
		    (vector-set! results i result))
		  (with-thread-mutex-locked lock
		    (lambda ()
		      (assert (< 0 n))
		      (set! n (- n 1))
		      (condition-variable-signal! condvar)))))))))
      (with-thread-mutex-locked lock
	(lambda ()
	  (do () ((zero? n))
	    (condition-variable-wait! condvar lock))))
      (vector->list results))))
