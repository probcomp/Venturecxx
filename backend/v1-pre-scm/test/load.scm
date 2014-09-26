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
      check
      register-test
      make-single-test
      detect-docstring
      generate-test-name
      better-message
      assert-proc
      run-tests-and-exit
      run-registered-tests)))

(load-relative "stats")

(define-each-check
  (equal? (top-eval 1) 1)
  (equal? (top-eval '((lambda () 1))) 1)
  (equal? (top-eval '((lambda (x) 1) 2)) 1)
  (equal? (top-eval '((lambda (x) x) 2)) 2)
  (equal? (top-eval '((lambda (x) (atomically x)) 3)) 3)
  (equal? (top-eval '((atomically (lambda (x) (atomically x))) 4)) 4)
  (equal? (top-eval '(+ 3 2)) 5)
  (equal? (top-eval '(((lambda (x) (lambda (y) (+ x y))) 3) 4)) 7)
  (equal? (top-eval '(((lambda (x) (atomically (lambda (y) (+ x y)))) 3) 4)) 7)
  (equal? (top-eval '(begin (+ 2 3) (* 2 3))) 6)
  (equal? (top-eval
           `(begin
              ,map-defn
              (map (lambda (x) (+ x 1)) (list 1 2 3))))
          '(2 3 4))
  (boolean? (top-eval inference-smoke-test-defn))
  ((lambda (items)
     (and (boolean? (car items))
          (boolean? (cadr items)))) (top-eval inference-smoke-test-2-defn))
  (equal? (top-eval '(model-in (rdb-extend (get-current-trace))
                               (assume x 4)
                               (predict x))) 4)
  )

(define *num-samples* 20)

(define two-coin-flipping-example
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.5))
       (assume c2 (flip 0.5))
       (observe (flip (if (boolean/or c1 c2) 1 0.0001)) #t)
       (infer (mcmc 20))
       (predict c1))))

(define-test (two-coin-dist)
  (let ()
    (define samples (map (lambda (i)
                           (top-eval two-coin-flipping-example))
                         (iota *num-samples*)))
    (check (> (chi-sq-test samples '((#t . 2/3) (#f . 1/3))) 0.001))))

(define two-coins-with-brush-example
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume c1 (flip 0.5))
       (assume c2 (if c1 #t (flip 0.5)))
       (observe (flip (if (boolean/or c1 c2) 1 0.0001)) #t)
       (infer (mcmc 20))
       (predict c1))))

(define-test (two-coin-brush-dist)
  (let ()
    (define samples (map (lambda (i)
                           (top-eval two-coins-with-brush-example))
                         (iota *num-samples*)))
    (check (> (chi-sq-test samples '((#t . 2/3) (#f . 1/3))) 0.001))))

(define-test (forward-normal-dist)
  (let ()
    (define samples (map (lambda (i)
                           (pp i)
                           (top-eval `(begin ,gaussian-defn (normal 0 1))))
                         (iota *num-samples*)))
    (pp (list 'program-samples (sort samples <)))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 0 1))) 0.001))))

(define-test (observed-normal-dist)
  (let ()
    (define samples (map (lambda (i)
                           (pp i)
                           (top-eval gaussian-example))
                         (iota *num-samples*)))
    (pp (list 'program-samples (sort samples <)))
    (check (> (k-s-test samples (lambda (x) (gaussian-cdf x 1 (/ 1 (sqrt 2))))) 0.001))))
