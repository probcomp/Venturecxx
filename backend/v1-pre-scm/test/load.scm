(define (self-relatively thunk)
  (if (current-eval-unit #f)
      (with-working-directory-pathname
       (directory-namestring (current-load-pathname))
       thunk)
      (thunk)))

(define (load-relative filename #!optional environment)
  (self-relatively (lambda () (load filename environment))))

(define test-environment (make-top-level-environment))

(load-relative "../testing/load" test-environment)

(let ((client-environment (the-environment)))
  (for-each
   (lambda (n)
     (environment-link-name client-environment test-environment n))
   '( define-each-check
      register-test
      make-single-test
      detect-docstring
      generate-test-name
      better-message
      assert-proc
      run-tests-and-exit)))

(define-each-check
  (equal? (top-eval 1) 1))

