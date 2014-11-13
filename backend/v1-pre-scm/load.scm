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

(define scheme-apply (access apply system-global-environment))

(load-relative "adaptive-plot/load")

;; The gnuplot code uses apply so needs protection
(define gnuplot-environment (make-top-level-environment))
(load-relative-compiled "gnuplot" gnuplot-environment)
(let ((client-environment (the-environment)))
  (for-each
   (lambda (n)
     (environment-link-name client-environment gnuplot-environment n))
   '( gnuplot-multiple
      gnuplot-alist
      gnuplot-alist-plot
      gnuplot-histogram-alist
      gnuplot-histogram-alist-plot
      gnuplot-direct-to-file
      )))

(load-relative "pattern-case/load")
(load-relative-compiled "utils")
(load-relative-compiled "small-exact")
(load-relative-compiled "syntax")
(load-relative-compiled "address")
(load-relative-compiled "v1-pre")
(load-relative-compiled "primitives")
(load-relative-compiled "random-db")
(load-relative-compiled "rdb-constraint-propagation")
(load-relative-compiled "scaffolds")
(load-relative-compiled "inference")
(load-relative-compiled "store")
(load-relative-compiled "gaussian")

(define (re-run-test test) (load "load") (load "test/load") (run-test test))

#|
Instructions from Taylor on how to use the multiprocess parallelism:

# Run the server.
scheme --batch-mode --load match --load condvar --load remote-io --load remote-balancer --eval '(run-venture-load-balancer 12345 (lambda (service) (pp `(server "127.0.0.1:12345" ,(unix/current-pid)))))' &

# Start some workers.
for i in 0 1 2 4 5 6 7; do scheme --batch-mode --load load --load match --load condvar --load remote-io --load remote-worker --eval '(run-venture-worker 12345 (lambda () (pp `(worker ,(unix/current-pid)))))' & done

# Now load it up and try it.
scheme --batch-mode --load match --load condvar --load remote-io --load remote-client --eval '(begin (pp (venture-remote-eval* 12345 (map (lambda (i) `(expt 2 ,i)) (iota 60)))) (%exit 0))'
|#
