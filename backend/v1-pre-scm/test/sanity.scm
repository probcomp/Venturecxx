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

