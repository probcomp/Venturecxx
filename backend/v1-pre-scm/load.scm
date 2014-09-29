(define (self-relatively thunk)
  (if (current-eval-unit #f)
      (with-working-directory-pathname
       (directory-namestring (current-load-pathname))
       thunk)
      (thunk)))

(define (load-relative filename #!optional environment)
  (self-relatively (lambda () (load filename environment))))

(load-relative "auto-compilation")

;; This appears to need to be run interpreted? Is constant folding
;; screwing me up?
(define minus-inf
  (flo:with-exceptions-untrapped (flo:exception:divide-by-zero)
     (lambda ()
       (flo:/ -1. 0.))))

(define gnuplot-environment (make-top-level-environment))

(load-relative-compiled "gnuplot" gnuplot-environment)

(let ((client-environment (the-environment)))
  (for-each
   (lambda (n)
     (environment-link-name client-environment gnuplot-environment n))
   '( gnuplot-multiple
      gnuplot-alist
      gnuplot-histogram-alist)))

(define scheme-apply (access apply system-global-environment))

(load-relative "pattern-case/load")
(load-relative-compiled "utils")
(load-relative-compiled "syntax")
(load-relative-compiled "v1-pre")
(load-relative-compiled "primitives")
(load-relative-compiled "random-db")
(load-relative-compiled "store")
(load-relative-compiled "gaussian")
