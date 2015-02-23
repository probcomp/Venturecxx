;;; Network I/O utilities.

(declare (usual-integrations))

(define (network-error)
  (error "Network error!"))

(define (call-with-local-tcp-server-socket service receiver)
  (let ((socket (open-tcp-server-socket service (host-address-loopback))))
    (listen-tcp-server-socket socket)
    (begin0 (receiver socket)
      (close-tcp-server-socket socket))))

(define (call-with-local-tcp-stream-socket service receiver)
  (let ((socket (open-tcp-stream-socket "127.0.0.1" service)))
    (begin0 (receiver socket)
      (close-port socket))))

(define (call-with-accept-socket server-socket receiver)
  (let ((socket (tcp-server-connection-accept server-socket #t #f)))
    (assert (port? socket))
    (begin0 (receiver socket)
      (close-port socket))))

(define hex-digits "0123456789abcdef")
(define char-set:hex (string->char-set hex-digits))

(define (network-read socket)
  (let* ((size-buf (make-string 6))
	 (size-n (read-substring! size-buf 0 6 socket)))
    (if (not (eqv? size-n 6))
	(network-error))
    (if (string-find-next-char-in-set size-buf (char-set-invert char-set:hex))
	(network-error))
    ;; XXX Use a safer parser than STRING->NUMBER.
    (let* ((size (string->number size-buf #x10))
	   (buf (make-string size))
	   (n (read-substring! buf 0 size socket)))
      (if (not (eqv? n size))
	  (network-error))
      ;; XXX Don't expose READ to the network.
      (read (open-input-string buf)))))

(define (network-write socket message)
  (let* ((buf (write-to-string message))
	 (size (string-length buf)))
    ;; XXX Hmm...  Assertion is sketchy here.
    (assert (<= size (expt 2 (* 6 4))))
    (let ((size-buf (make-string 6)))
      (let loop ((i 6) (s size))
	(if (< 0 i)
	    (let ((i (- i 1))
		  (h (string-ref hex-digits (bitwise-and s #xf))))
	      (string-set! size-buf i h)
	      (loop i (shift-right s 4)))))
      (write-substring size-buf 0 6 socket))
    (write-substring buf 0 size socket))
  (flush-output socket))

(define (condition->string condition)
  (call-with-output-string
    (lambda (port)
      (write-condition-report condition port))))

(define (spawn-thread procedure)
  (let ((root-continuation (create-thread-continuation)))
    (create-thread root-continuation
      (lambda ()
	(with-create-thread-continuation root-continuation procedure)))))

(define (thread-mutex-owned? mutex)
  (eq? (current-thread) (thread-mutex-owner mutex)))