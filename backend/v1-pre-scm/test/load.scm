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
      define-test
      in-test-group
      *current-test-group* ; pulled in by macro
      tg:find-or-make-subgroup ; pulled in by macro
      check
      register-test
      make-single-test
      detect-docstring
      generate-test-name
      better-message
      assert-proc
      run-tests-and-exit
      run-registered-tests
      run-test
      assert-true)))

(load-relative "stats")

(define *num-samples* 50)

(define (collect-samples prog #!optional count)
  (map (lambda (i)
         ; (pp `(running ,i))
         (top-eval prog))
       (iota (if (default-object? count) *num-samples* count))))

(define *p-value-tolerance* 0.01)

(load-relative "sanity")
(load-relative "discrete")
(load-relative "continuous")
(load-relative "overincorporation")
