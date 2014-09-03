(define (self-relatively thunk)
  (if (current-eval-unit #f)
      (with-working-directory-pathname
       (directory-namestring (current-load-pathname))
       thunk)
      (thunk)))

(define (load-relative filename #!optional environment)
  (self-relatively (lambda () (load filename environment))))

(load-relative "pattern-case/load")
(load-relative "utils")
(load-relative "syntax")
(load-relative "v1-pre")
(load-relative "primitives")
(load-relative "random-db")
(load-relative "store")
