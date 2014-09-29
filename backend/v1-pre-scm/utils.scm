(declare (usual-integrations))

(define-syntax aif
  (sc-macro-transformer
   (lambda (exp env)
     (let ((ctest (close-syntax (cadr exp) env))
	   (cthen (make-syntactic-closure env '(it) (caddr exp)))
	   (celse (if (pair? (cdddr exp))
		      (list (close-syntax (cadddr exp) env))
		      '())))
       `(let ((it ,ctest))
	  (if it ,cthen ,@celse))))))

(define-syntax abegin1
  (sc-macro-transformer
   (lambda (exp env)
     (let ((object (close-syntax (cadr exp) env))
	   (forms (map (lambda (form)
                         (make-syntactic-closure env '(it) form))
                       (cddr exp))))
       `(let ((it ,object))
	  ,@forms
          it)))))

(define (search-parallel-lists item keys vals win lose #!optional =)
  (if (default-object? =)
      (set! = eq?))
  (let loop ((ks keys)
             (vs vals))
    (cond ((null? ks)
           (lose))
          ((= (car ks) item)
           (win (car vs)))
          (else (loop (cdr ks) (cdr vs))))))

(define *binwidth* 0.2)

(define (histogram-test-data data)
  (gnuplot-histogram-alist (map (lambda (x) (cons x *binwidth*)) data) "test data" *binwidth*))

(define (compare-data-to-cdf samples analytic . adverbs)
  (let* ((samples (sort samples <))
         (n (length samples))
         (xlow (scheme-apply min samples))
         (xhigh (scheme-apply max samples))
         (padding (* 0.1 (- xhigh xlow)))
         (cdf-plot (plot-stop-drawing!
                    (scheme-apply replot (new-plot analytic (- xlow padding) (+ xhigh padding)) 'invisibly adverbs)))
         (empirical (append-map
                     (lambda (x i)
                       (list (cons x (/ i n)) (cons x (/ (+ i 1) n))))
                     samples (iota n))))
    (call-with-temporary-file-pathname
     (lambda (empirical-pathname)
       (call-with-temporary-file-pathname
        (lambda (analytic-pathname)
          (gnuplot-write-alist empirical empirical-pathname)
          (gnuplot-write-alist (plot-relevant-points-alist cdf-plot) analytic-pathname)
          (let ((command (string-append
                          "gnuplot -p -e \'"
                          "set style data lines; "
                          "set key noautotitles; "
                          "plot \"" (->namestring empirical-pathname) "\" title \"empirical\""
                          ", \"" (->namestring analytic-pathname) "\" title \"analytic\""
                          "'")))
            (display command)
            (newline)
            (run-shell-command command))))))))
