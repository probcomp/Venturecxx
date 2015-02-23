;;; Venture remote evaluation load balancer for parallelism.

;;; Run one load balancer.  Run n workers pointed at it.  When you
;;; point a client at the load balancer, it will dispatch the request
;;; to one of the workers and return a result.
;;;
;;; XXX Maybe it should be called `dispatcher' instead of `load
;;; balancer.'

(declare (usual-integrations))

(define-structure (load-balancer (constructor make-load-balancer ()))
  (lock (make-thread-mutex) read-only #t)
  (condvar (make-condition-variable "venture-load-balancer") read-only #t)
  (dying? #f)
  (workqueue (make-queue)))

(define-structure (work (constructor make-work (program/result)))
  (lock (make-thread-mutex) read-only #t)
  (condvar (make-condition-variable "venture-work") read-only #t)
  (done? #f)
  (retries 3)				;XXX Make configurable.
  program/result)

(define (work-done! work result)
  (with-thread-mutex-locked (work-lock work)
    (lambda ()
      (%work-done! work result))))

(define (%work-done! work result)
  (assert (thread-mutex-owned? (work-lock work)))
  (set-work-program/result! work result)
  (set-work-done?! work #t)
  (condition-variable-broadcast! (work-condvar work)))

(define (queue-work! work lbr)
  (with-thread-mutex-locked (load-balancer-lock lbr)
    (lambda ()
      (%queue-work! work lbr))))

(define (%queue-work! work lbr)
  (assert (thread-mutex-owned? (load-balancer-lock lbr)))
  (enqueue! (load-balancer-workqueue lbr) work)
  (condition-variable-signal! (load-balancer-condvar lbr)))

(define (retry-work! work lbr)
  ((with-thread-mutex-locked (work-lock work)
     (lambda ()
       (if (zero? (work-retries work))
	   (begin
	     (%work-done! work '(FAIL))
	     (lambda () 0))
	   (begin
	     (set-work-retries! work (- (work-retries work) 1))
	     (lambda ()
	       (queue-work! work lbr))))))))

(define (run-venture-load-balancer service when-ready)
  (let ((lbr (make-load-balancer)))
    (call-with-local-tcp-server-socket service
      (lambda (server-socket)
	(when-ready service)
	(let loop ()
	  (let* ((socket (tcp-server-connection-accept server-socket #t #f))
		 (id (ignore-errors (lambda () (network-read socket)))))
	    (case id
	      ((CLIENT) (lbr:serve-thread lbr:serve-client lbr socket) (loop))
	      ((WORKER) (lbr:serve-thread lbr:serve-worker lbr socket) (loop))
	      ((TERMINATE) (lbr:terminate lbr) (close-port socket))
	      (else (close-port socket) (loop)))))))))

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
			 (work-done! (dequeue! queue) '(FAIL))
			 (loop))))))))))))

(define (lbr:serve-thread serve lbr socket)
  (spawn-thread
    (lambda ()
      ;; XXX Log errors somewhere.
      (dynamic-wind
       (lambda () 0)
       (lambda () (serve lbr socket))
       (lambda () (ignore-errors (lambda () (close-port socket))))))))

(define (lbr:serve-client lbr socket)
  (match (network-read socket)
    (`(EVAL ,program)
     ((with-thread-mutex-locked (load-balancer-lock lbr)
	(lambda ()
	  (if (load-balancer-dying? lbr)
	      (lambda ()
		(network-write socket '(FAIL)))
	      (let ((work (make-work program)))
		(%queue-work! work lbr)
		(lambda ()
		  (with-thread-mutex-locked (work-lock work)
		    (lambda ()
		      (do () ((work-done? work))
			;; XXX Simultaneously wait for a nack on the network.
			(condition-variable-wait! (work-condvar work)
						  (work-lock work)))))
		  (network-write socket (work-program/result work)))))))))))

(define (lbr:serve-worker lbr socket)
  (let loop ()
    ((with-thread-mutex-locked (load-balancer-lock lbr)
       (lambda ()
	 (cond ((load-balancer-dying? lbr)
		(lambda ()
		  (network-write socket '(TERMINATE))
		  0))
	       ((queue-empty? (load-balancer-workqueue lbr))
		(condition-variable-wait! (load-balancer-condvar lbr)
					  (load-balancer-lock lbr))
		(lambda ()
		  (loop)))
	       (else
		(let ((work (dequeue! (load-balancer-workqueue lbr))))
		  (lambda ()
		    (call-with-current-continuation
		     (lambda (abort)
		       (bind-condition-handler (list condition-type:error)
			   (lambda (condition)
			     condition	;XXX Log this.
			     ;; Worker has died.  Let another one
			     ;; take it instead, and give up on
			     ;; running this one.
			     (retry-work! work lbr)
			     (abort 0))
			 (lambda ()
			   (network-write
			    socket
			    `(EVAL ,(work-program/result work)))
			   (work-done! work (network-read socket))))
		       (loop))))))))))))