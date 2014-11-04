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
		  (ignore-errors
		   (lambda ()
		     (match (network-read socket)
		       (`(EVAL ,program)
			(network-write socket `(OK ,(top-eval program)))))))
		  loop)
		 ((TERMINATE) (lambda () 0))
		 (else loop))))))))))