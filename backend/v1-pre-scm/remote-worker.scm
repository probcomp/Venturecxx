;;; Venture remote evaluation load balancer worker.

(declare (usual-integrations))

(define (run-venture-worker service)
  (call-with-local-tcp-stream-socket service
    (lambda (socket)
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