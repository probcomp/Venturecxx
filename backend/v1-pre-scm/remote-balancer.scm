;;; Venture remote evaluation load balancer for parallelism.

;;; Run one load balancer.  Run n workers pointed at it.  When you
;;; point a client at the load balancer, it will dispatch the request
;;; to one of the workers and return a result.

(declare (usual-integrations))

(define-structure load-balancer
  (lock (make-thread-mutex))
  (condvar (make-condition-variable "venture-load-balancer"))
  (dying? #f)
  (workqueue (make-queue)))

(define-structure (work (constructor make-work (program/result)))
  (lock (make-thread-mutex))
  (condvar (make-condition-variable "venture-work"))
  (state work:pending)
  program/result)

(define work:pending 0)
(define work:done 1)
(define work:failed -1)

(define (run-venture-load-balancer service)
  (let ((server-socket (open-tcp-server-socket service)))
    (let loop ()
      (let* ((socket (listen-tcp-server-socket server-socket))
	     (id (ignore-errors (lambda () (network-read socket)))))
	(case id
	  ((CLIENT) (lbr:server-thread lbr:serve-client lbr socket) (loop))
	  ((WORKER) (lbr:server-thread lbr:serve-worker lbr socket) (loop))
	  ((TERMINATE) (lbr:terminate lbr) (close-port socket))
	  (else (close-port socket) (loop)))))))

(define (lbr:terminate lbr)
  ((with-thread-mutex-locked (load-balancer-lock lbr)
     (lambda ()
       (if (load-balancer-dying? lbr)
	   (lambda () 0)
	   (begin
	     (set-load-balancer-dying?! lbr #t)
	     (condition-variable-broadcast! (load-balancer-condvar lbr))
	     (let ((queue (load-balancer-workqueue lbr)))
	       (set-load-balancer-workqueue! lbr 0)
	       (lambda ()
		 (let loop ()
		   (if (not (queue-empty? queue))
		       (begin
			 (let ((work (dequeue! queue)))
			   (with-thread-mutex-locked (work-lock work)
			     (lambda ()
			       (set-work-state! work work:failed)
			       (condition-variable-broadcast!
				(work-condvar work)))))
			 (loop))))))))))))

(define (lbr:server-thread run lbr socket)
  (create-thread #f
    (lambda ()
      (dynamic-wind
       (lambda () 0)
       (lambda () (run lbr socket))
       (lambda () (close-socket socket))))))

(define (lbr:serve-client lbr socket)
  (match (network-read socket)
    (`(EVAL ,program)
     ((with-thread-mutex-locked (load-balancer-lock lbr)
	(lambda ()
	  (if (load-balancer-dying? lbr)
	      (lambda ()
		(network-write socket '(FAIL)))
	      (begin
		(enqueue! (load-balancer-workqueue lbr) work)
		(lambda ()
		  (with-thread-mutex-locked (work-lock work)
		    (lambda ()
		      (do () ((eqv? (work-state work) work:pending))
			;; XXX Simultaneously wait for a nack on the network.
			(condition-variable-wait! (work-condvar work)
						  (work-lock work)))))
		  (network-write socket
				 (if (eqv? (work-state work) work:done)
				     `(OK ,(work-program/result work))
				     '(FAIL))))))))))))

(define (lbr:serve-worker lbr socket)
  (let loop ()
    ((with-thread-mutex-locked (load-balancer-lock lbr)
       (lambda ()
	 (cond ((load-balancer-dying? lbr)
		(lambda ()
		  (network-write socket '(FAIL))
		  0))
	       ((queue-empty? (load-balancer-workqueue lbr))
		(condition-variable-wait! (load-balancer-condvar lbr)
					  (load-balancer-lock lbr))
		(lambda ()
		  (loop)))
	       (else
		(let ((work (dequeue! (load-balancer-workqueue lbr))))
		  (lambda ()
		    (network-write socket `(EVAL ,(work-program/result work)))
		    (match (network-read socket)
		      (`(OK ,result)
		       (with-thread-mutex-locked (work-lock work)
			 (lambda ()
			   (set-work-program/result! work result)
			   (set-work-state! work work:done)
			   (condition-variable-broadcast!
			    (work-condvar work)))))
		      (else
		       (with-thread-mutex-locked (work-lock work)
			 (lambda ()
			   (set-work-program/result! work 0)
			   (set-work-state! work work:failed)
			   (condition-variable-broadcast!
			    (work-condvar work))))))
		    (loop))))))))))
