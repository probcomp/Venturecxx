;;; Venture remote evaluation load balancer worker.

(declare (usual-integrations))

(define (run-venture-worker host service)
  (call-with-tcp-stream-socket host service
    (lambda (socket)
      ;; This is worker, hello!
      (network-write socket 'WORKER)
      (let loop ()
	(match (network-read socket)
	  (`(EVAL ,program)
	   (network-write socket `(OK ,(top-eval program)))
	   (loop)))))))
