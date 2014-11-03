
(define *scmserver* (create-rpc-server))


; id symbol, salt, password hash, procedure

(define *scmserver-service-table*
  `((test "1234" "9†·≥\b'\212\215Â‡\aÕ\037yY " ,(lambda () 'test))
    (eval "1234" "9†·≥\b'\212\215Â‡\aÕ\037yY " ,(lambda (x) (eval x user-generic-environment)))))


(define (scmserver-accessor requested-thing-id password)
  (let ((thing-record (assoc requested-thing-id *scmserver-service-table*)))
    (if (not thing-record)
	(error 'unknown-service-id requested-thing-id)
	(let* ((salt (cadr thing-record))
	       (salted-pw (string-append salt password))
	       (salted-hash (md5-string salted-pw)))
	  (if (string=? salted-hash (caddr thing-record))
	      (cadddr thing-record)
	      (begin
		(sleep-current-thread 1000)
		(error 'unauthorized)))))))


(register-rpc-procedure *scmserver* "access-thing" scmserver-accessor)


(define (server-start #!optional port address)
  (let ((port (if (default-object? port) 6674 port))
	(address (if (default-object? address) (host-address-any) address)))
    (start-rpc-server *scmserver* port address)))


(define (server-stop)
  (stop-rpc-server *scmserver*))



;;;
;;; Client:

(define (client-connect port host)
  (let ((client (create-rpc-client)))
    (connect-rpc-client client port host)
    client))

(define (client-disconnect client)
  (disconnect-rpc-client client))

(define (client-access-service client service-id password)
  ((bind-rpc-call client "access-thing")
   service-id password))

#|
;;;;  Demo
;;; Assume that the password is "foo".

(define client (client-connect 6674 "maharal.csail.mit.edu"))
#| client |#

(define foosh
  (client-access-service client
			 'test
			 "foo"))
#| foosh |#

(foosh)
#| test |#


(define baz
  (client-access-service client
			 'eval

(baz 0)
#| 0 |#

(baz '(simplify '(/ 1 (+ (/ 1 r1) (/ 1 r2)))))
#|
(/ (* r1 r2) (+ r1 r2))
|#
|#