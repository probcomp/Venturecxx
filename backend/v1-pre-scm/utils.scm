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

(define (kdensity-test-data data)
  (let ((n (length data)))
    (gnuplot-alist (map (lambda (x) (cons x (/ 1 n))) data) '(commanding "title \"data\" smooth kdensity") )))

(define (gnuplot-function-plot-near f data . adverbs)
  (let* ((n (length data))
         (xlow (scheme-apply min data))
         (xhigh (scheme-apply max data))
         (padding (* 0.1 (- xhigh xlow)))
         (cdf-plot (plot-stop-drawing!
                    (scheme-apply replot (new-plot f (- xlow padding) (+ xhigh padding)) 'invisibly adverbs))))
    (scheme-apply gnuplot-alist-plot (plot-relevant-points-alist cdf-plot) adverbs)))

(define (compare-data-to-cdf samples analytic . adverbs)
  (let* ((samples (sort samples <))
         (n (length samples))
         (empirical (append-map
                     (lambda (x i)
                       (list (cons x (/ i n)) (cons x (/ (+ i 1) n))))
                     samples (iota n))))
    (gnuplot-multiple
     (list
      (gnuplot-alist-plot empirical '(commanding "title \"empirical CDF\""))
      (gnuplot-function-plot-near analytic samples '(commanding "title \"analytic CDF\""))))))

(define (compare-kdensity-to-pdf samples analytic)
  (let ((n (length samples)))
    (gnuplot-multiple
     (list
      (gnuplot-alist-plot (map (lambda (x) (cons x (/ 1 n))) samples)
                          '(commanding "title \"empirical kernel density\" smooth kdensity"))
      (gnuplot-function-plot-near analytic samples '(commanding "title \"analytic density\""))))))

(define (compare-histogram-to-pdf samples analytic)
  (let ((n (length samples)))
    (gnuplot-multiple
     (list
      (gnuplot-histogram-alist-plot (map (lambda (x) (cons x (/ 1 n))) samples)
                                    "empirical histogram" *binwidth*)
      (gnuplot-function-plot-near analytic samples '(commanding "title \"analytic density\""))))))
