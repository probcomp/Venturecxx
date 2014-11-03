;;; Client:

(define mechanics-port 9807)

(define (client-connect #!optional host port)
  (let ((client (create-rpc-client))
	(port (if (default-object? port) mechanics-port port))
	(address (if (default-object? host) (host-address-any) host)))
    (connect-rpc-client client port address)
    client))

(define (client-disconnect client)
  (disconnect-rpc-client client))

(define (client-access-service client service-id password)
  ((bind-rpc-call client "access-thing")
   service-id password))


#|
;;;;  Demo
;;; Assume that the password is "foo".

(define client (client-connect "127.0.0.1" mechanics-port))
;Value: client

(define reval
  (client-access-service client 'eval "foo"))
;Value: reval

(define env
  ((client-access-service client 'new-env "foo")))
;Value: env

(reval '|:G| env)
;Value: (*with-units* .0000000000667428 (*unit* si #(3 -1 -2 0 0 0 0) 1))

(reval '(define foo 3) env)
;Value: foo

(reval 'foo env)
;Value: 3

(define env1
  ((client-access-service client 'new-env "foo")))
;Value: env1

(reval 'foo env)
;Value: 3

(reval 'foo env1)
; rpc-remote-error-raised #(remote-condition "Unbound variable: foo" "Subproblem level: 0 (this is the lowest subproblem level)\nExpression (from stack):\n    foo\nEnvironment created by a LAMBDA special form\n\n applied to: ()\nThere is no execution history for this subproblem.\n\nSubproblem level: 1\nExpression (from stack):\n    (success ###)\n subproblem being executed (marked by ###):\n    (with-error-filter (lambda (condition) (k (fail condition)))\n                       (lambda () (apply handler args)))\nEnvironment created by a LET special form\n\n applied to: (#[compile...")
;Quit!

(reval '(define foo 4) env1)
;Value: foo

(reval 'foo env)
;Value: 3

(reval 'foo env1)
;Value: 4

(reval '(simplify '(/ 1 (+ (/ 1 r1) (/ 1 r2)))) env)
;Value: (/ (* r1 r2) (+ r1 r2))

(client-disconnect client)
|#