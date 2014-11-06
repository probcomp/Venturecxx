(declare (usual-integrations))

(define-syntax test-equal
  (syntax-rules ()
    ((TEST-EQUAL expected actual)
     (LET ((E expected)
	   (A actual))
       (IF (NOT (EQUAL? E A))
	   (BEGIN
	     (ERROR "Not equal:"
		    'actual (error-irritant/noise " gave") A
		    (error-irritant/noise " but expected") E
		    (error-irritant/noise " from") 'expected)
	     ;; Force the relevant variables to remain in the environment.
	     (REFERENCE-BARRIER (LIST expected actual))))))))

(define-syntax test-error
  (syntax-rules ()
    ((TEST-ERROR expression)
     (CALL-WITH-CURRENT-CONTINUATION
      (LAMBDA (K)
	(BIND-CONDITION-HANDLER (LIST CONDITION-TYPE:ERROR)
	    (LAMBDA (CONDITION)
	      CONDITION			;ignore
	      (K 0))
	  (LAMBDA ()
	    (ERROR "Failed to signal error:" 'expression
		   (error-irritant/noise " gave") expression)
	    (REFERENCE-BARRIER expression))))))))

(define (with-timeout timeout on-timeout procedure)
  (let ((registration))
    (dynamic-wind
     (let ((registered? #f))
       (lambda ()
	 (if registered? (error "Re-entry into timeout zone!"))
	 (set! registered? #t)
	 (set! registration (register-timer-event timeout on-timeout))))
     procedure
     (lambda ()
       (deregister-timer-event registration)))))

(define-syntax with*
  (syntax-rules ()
    ((WITH* () body0 body1+ ...)
     (BEGIN body0 body1+ ...))
    ((WITH* ((x (f0 f1+ ...)) (y (g+0 g+1+ ...)) ...) body0 body1+ ...)
     (f0 f1+ ...
       (LAMBDA x (WITH* ((y (g+0 g+1+ ...)) ...) body0 body1+ ...))))))

(define-syntax with
  (syntax-rules ()
    ((WITH ((v (f0 f1+ ...)) ...) body0 body1+ ...)
     (WITH* (((v) (f0 f1+ ...)) ...) body0 body1+ ...))))

(define (temporary-thread procedure body)
  (let* ((barrier (make-thread-barrier 2))
	 (thread
	  (spawn-thread
            (lambda ()
	      (procedure (lambda () (thread-barrier-wait barrier)))))))
    (dynamic-wind
     (let ((done? #f))
       (lambda ()
	 (if done? (error "Re-entry into temporary thread zone!"))
	 (set! done? #t)
	 0))
     (lambda ()
       (thread-barrier-wait barrier)
       (body thread))
     (lambda ()
       (terminate-thread thread)
       ;; Force close file descriptors.  XXX Whattakludge!
       (gc-flip)))))

(define (terminate-thread thread)
  ;; XXX Whattakludge!
  (define (exit) (exit-current-thread 0))
  (ignore-errors (lambda () (signal-thread-event thread exit)))
  (ignore-errors (lambda () (restart-thread thread #f exit))))

(define (test-network-read/write message)
  (let* ((wire-format
	  (call-with-output-string
	    (lambda (port)
	      (network-write port message))))
	 (message*
	  (call-with-input-string wire-format
	    (lambda (port)
	      (network-read port)))))
    (test-equal message* message)))

(test-network-read/write 0)
(test-network-read/write 1)
(test-network-read/write 'foo)
(test-network-read/write "")
(test-network-read/write "bar")
(test-network-read/write '(0 1 foo "bar"))
(test-network-read/write '())

(define (server service body)
  (temporary-thread
      (lambda (when-ready)
	(run-venture-server service
	  (lambda (service*)
	    (assert (eqv? service service*))
	    (when-ready))))
    body))

(define (balancer service body)
  (temporary-thread
      (lambda (when-ready)
	(run-venture-load-balancer service
	  (lambda (service*)
	    (assert (eqv? service service*))
	    (when-ready))))
    body))

(define (worker service body)
  (temporary-thread
      (lambda (when-ready)
	(run-venture-worker service when-ready))
    body))

(define (join-thread-sync thread)
  (let ((done? #f)
	(value))
    (join-thread thread
		 (lambda (thread result)
		   thread		;ignore
		   (lambda ()
		     (set! done? #t)
		     (set! value result))))
    (do () (done?)
      (suspend-current-thread))
    value))

(define (client/server body)
  (let ((service 12345))
    (with ((server (server service)))
      (begin0 (body service)
	(venture-remote-terminate service)
	(join-thread-sync server)))))

(define (client/balancer/worker body)
  (let ((service 12345))
    (with ((balancer (balancer service))
	   (worker (worker service)))
      (begin0 (body service)
	(venture-remote-terminate service)
	(join-thread-sync balancer)
	(join-thread-sync worker)))))

(define (test-null setup)
  (with ((service (setup)))
    service				;ignore
    0))

(define (test-eval setup program result)
  (test-equal result
    (with ((service (setup)))
      (venture-remote-eval service program))))

(define (test-eval* setup programs results)
  (test-equal results
    (with ((service (setup)))
      (venture-remote-eval* service programs))))

(define (test-eval-error setup program)
  ;; XXX Test the nature of the error.
  (test-error
    (with ((service (setup)))
      (venture-remote-eval service program))))

(define (test-eval*-error setup programs)
  ;; XXX Test the nature of the errors.
  ;; XXX Partial success.
  (test-error
    (with ((service (setup)))
      (venture-remote-eval* service programs))))

((lambda (checkem)
   (for-each (lambda (setup)
	       (for-each (lambda (test)
			   (with-timeout 1000
			       (lambda ()
				 (error "Test timed out!" setup test))
			     (lambda ()
			       (test setup))))
			 checkem))
	     (list client/server client/balancer/worker)))
 (list
  (lambda (setup) (test-null setup))
  (lambda (setup) (test-eval setup 0 0))
  (lambda (setup) (test-eval setup '(+ 1 2) 3))
  (lambda (setup) (test-eval* setup '((+ 1 2) (* 3 4)) '(3 12)))
  (lambda (setup) (test-eval-error setup 'an-undefined-variable))
  (lambda (setup)
    (test-eval*-error setup '((+ 1 2) an-undefined-variable (* 3 4))))))
