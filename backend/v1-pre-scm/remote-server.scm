;;; Trivial single-threaded server.  Not useful for parallelization.
;;; Useful perhaps for testing.

(declare (usual-integrations))

(define (run-venture-server service)
  (call-with-tcp-server-socket service
    (lambda (server-socket)
      (let loop ()
	(let* ((socket (listen-tcp-server-socket server-socket))
	       (id (ignore-errors (lambda () (network-read socket)))))
	  (case id
	    ((CLIENT)
	     (dynamic-wind
	      (lambda () 0)
	      (lambda ()
		(match (network-read socket)
		  (`(EVAL ,program)
		   (network-write socket `(OK ,(top-eval program))))))
	      (lambda () (close-port socket)))
	     (loop))
	    ((TERMINATE)
	     0)
	    (else
	     (close-port socket)
	     (loop))))))))