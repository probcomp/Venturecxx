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