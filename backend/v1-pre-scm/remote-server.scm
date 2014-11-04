;;; Trivial single-threaded server.  Not useful for parallelization.
;;; Useful perhaps for testing.

(declare (usual-integrations))

(define (run-venture-server service)
  (call-with-tcp-server-socket service
    (lambda (server-socket)
      (let loop ()
	((call-with-accept-socket server-socket
	   (lambda (socket)
	     (let ((id (ignore-errors (lambda () (network-read socket)))))
	       (case id
		 ((CLIENT)
		  (match (ignore-errors (lambda () (network-read socket)))
		    (`(EVAL ,program)
		     ((call-with-current-continuation
		       (lambda (abort)
			 (bind-condition-handler (list condition-type:error)
			     (lambda (condition)
			       (abort
				(lambda ()
				  (ignore-errors
				   (lambda ()
				     (network-write
				      socket
				      `(FAIL
					,(condition->string condition))))))))
			   (lambda ()
			     (let ((result (top-eval program)))
			       (lambda ()
				 (ignore-errors
				  (lambda ()
				    (network-write socket
						   `(OK ,result)))))))))))))
		  loop)
		 ((TERMINATE) (lambda () 0))
		 (else loop))))))))))

(define (condition->string condition)
  (call-with-output-string
    (lambda (port)
      (write-condition-report condition port))))