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

(define search-wt-tree
  (let ((unique (list 0)))
    (lambda (tree key win lose)
      (let ((result (wt-tree/lookup tree key unique)))
        (if (eq? unique result)
            (lose)
            (win result))))))

(define (wt-tree->alist tree)
  (let ((answer '()))
    (wt-tree/for-each (lambda (k v) (set! answer (cons (cons k v) answer))) tree)
    (reverse answer)))

(define (data< d1 d2)
  ;; Dammit, how many times have I written this program?
  (cond ((null? d1)
         (if (null? d2) #f #t))
        ((boolean? d1)
         (if (boolean? d2)
             (and d1 (not d2))
             #t))
        ((number? d1)
         (if (number? d2)
             (< d1 d2)
             #t))
        ((pair? d1)
         (if (pair? d2)
             (cond ((data< (car d1) (car d2)) #t)
                   ((equal? (car d1) (car d2))
                    (data< (cdr d1) (cdr d2)))
                   (else #f))
             #f))
        (else (error "Unsupported data" d1 d2))))

(define-syntax ensure
  (syntax-rules ()
    ((_ test arg ...)
     (if (test arg ...)
         'ok
         (error "Invariant violation" test arg ...)))))

(define (or/c . predicates)
  (lambda args
    (let loop ((predicates predicates))
      (if (null? predicates)
          #f
          (if (scheme-apply (car predicates) args)
              #t
              (loop (cdr predicates)))))))

(define (listof test)
  (lambda (item)
    (let loop ((item item))
      (cond ((null? item)
             #t)
            ((pair? item)
             (and (test (car item))
                  (loop (cdr item))))
            (else #f)))))

(define *binwidth* 0.2)

(define (samples->empirical-cdf-alist samples)
  (let ((samples (sort samples <))
        (n (length samples)))
    (append-map
     (lambda (x i)
       (list (cons x (/ i n)) (cons x (/ (+ i 1) n))))
     samples (iota n))))

(define (histogram-test-data data)
  (gnuplot-histogram-alist
   (map (lambda (x) (cons x *binwidth*)) data) "test data" *binwidth*))

(define (kdensity-test-data data)
  (let ((n (length data)))
    (gnuplot-alist
     (map (lambda (x) (cons x (/ 1 n))) data)
     '(commanding "title \"data\" smooth kdensity") )))

(define (gnuplot-empirical-cdf-plot samples #!optional title)
  (let* ((title (if (default-object? title)
                    "empirical CDF"
                    (string-append title " empirical CDF")))
         (command (string-append "title \"" title "\"")))
    (gnuplot-alist-plot
     (samples->empirical-cdf-alist samples) `(commanding ,command))))

(define (gnuplot-empirical-kde-plot samples #!optional title)
  (let* ((title (if (default-object? title)
                    "empirical kernel density"
                    (string-append title " empirical kernel density")))
         (command (string-append "title \"" title "\" smooth kdensity"))
         (n (length samples)))
    (gnuplot-alist-plot
     (map (lambda (x) (cons x (/ 1 n))) samples)
     `(commanding ,command))))

(define (gnuplot-empirical-histogram-plot samples #!optional title)
  (let* ((title (if (default-object? title)
                    "empirical histogram"
                    (string-append title " empirical histogram")))
         (n (length samples)))
    (gnuplot-histogram-alist-plot
     (map (lambda (x) (cons x (/ 1 n))) samples) title *binwidth*)))

(define (gnuplot-function-plot-near f data . adverbs)
  (let* ((n (length data))
         (xlow (scheme-apply min data))
         (xhigh (scheme-apply max data))
         (padding (* 0.1 (- xhigh xlow)))
         (cdf-plot (plot-stop-drawing!
                    (scheme-apply replot (new-plot f (- xlow padding) (+ xhigh padding))
                                  'invisibly adverbs))))
    (scheme-apply gnuplot-alist-plot (plot-relevant-points-alist cdf-plot) adverbs)))

(define (compare-data-to-cdf samples analytic . adverbs)
  (gnuplot-multiple
   (list
    (gnuplot-empirical-cdf-plot samples)
    (gnuplot-function-plot-near analytic samples '(commanding "title \"analytic CDF\"")))))

(define (compare-kdensity-to-pdf samples analytic)
  (gnuplot-multiple
   (list
    (gnuplot-empirical-kde-plot samples)
    (gnuplot-function-plot-near
     analytic samples '(commanding "title \"analytic density\"")))))

(define (compare-histogram-to-pdf samples analytic)
  (gnuplot-multiple
   (list
    (gnuplot-empirical-histogram-plot samples)
    (gnuplot-function-plot-near
     analytic samples '(commanding "title \"analytic density\"")))))

(define (compare-empirical-cdfs observed expected)
  (gnuplot-multiple
   (list
    (gnuplot-empirical-cdf-plot observed "observed")
    (gnuplot-empirical-cdf-plot expected "expected"))))

(define (compare-empirical-kdes observed expected)
  (gnuplot-multiple
   (list
    (gnuplot-empirical-kde-plot observed "observed")
    (gnuplot-empirical-kde-plot expected "expected"))))

;; This one is not actually very useful, written this way, because the
;; histograms overlap.
(define (compare-empirical-histograms observed expected)
  (gnuplot-multiple
   (list
    (gnuplot-empirical-histogram-plot observed "observed")
    (gnuplot-empirical-histogram-plot expected "expected"))))

(define (samples->inverse-cdf samples)
  (let ((n (length samples))
        (samples (list->vector samples)))
    (lambda (quantile)
      (let ((index (* n quantile)))
        (cond ((< index 1)
               minus-inf)
              ((and (<= 1 index) (< index n))
               (vector-ref samples (inexact->exact (floor (- index 1)))))
              (else
               (- minus-inf)))))))
