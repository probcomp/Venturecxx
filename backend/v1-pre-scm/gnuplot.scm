(declare (usual-integrations))

;;;; Gnuplot output of alist data

(load-option 'synchronous-subprocess)

(define (gnuplot-write-alist alist filename)
  (with-output-to-file filename
    (lambda ()
      (for-each
       (lambda (x.y)
	 (write (exact->inexact (car x.y)))
	 (display " ")
	 (write (exact->inexact (cdr x.y)))
	 (newline))
       alist))))

(define (gnuplot-alist alist . adverbs)
  (let ((gnuplot-extra (lax-alist-lookup adverbs 'commanding ""))
        (gnuplot-prefix (lax-alist-lookup adverbs 'prefixing "")))
    (call-with-temporary-file-pathname
     (lambda (pathname)
       (gnuplot-write-alist alist pathname)
       (let ((command (string-append
                       "gnuplot -p -e \'"
                       "set style data lines; "
                       "set key noautotitles; "
                       gnuplot-prefix
                       "; plot \""
                       (->namestring pathname)
                       "\" "
                       gnuplot-extra
                       "'")))
         (display command)
         (newline)
         (run-shell-command command))))))

(define (gnuplot-histogram-alist alist #!optional data-name binsize)
  ;; TODO Abstract the commonalities among these two
  (define (compute-bin-size numbers)
    (let* ((sorted (sort numbers <))
           (minimum (car sorted))
           (maximum (last sorted)))
      (/ (- maximum minimum) 200)))
  (if (default-object? binsize)
      (set! binsize (compute-bin-size (map car alist))))
  (call-with-temporary-file-pathname
   (lambda (pathname)
     (gnuplot-write-alist alist pathname)
     (let ((command (string-append
		     "gnuplot -p -e \'"
                     "binwidth=" (number->string binsize) "; "
                     "bin(x,width)=width*floor(x/width)+width/2; "
                     "set boxwidth binwidth; "
                     "set style fill solid; "
                     "plot \"" (->namestring pathname) "\" "
                     "using (bin($1,binwidth)):($2/binwidth) smooth freq with boxes "
                     (if (default-object? data-name) "" (string-append "title \"" data-name "\" "))
		     "'")))
       (display command)
       (newline)
       (run-shell-command command)))))

;; A "lax alist" is a list whose pairs are treated as alist elements,
;; but which is allowed to have non-pairs also (which are ignored).
(define (lax-alist-lookup alist item default #!optional =)
  (let ((binding (assoc item (filter pair? alist) =)))
    (if binding
        ;; I really want to be looking up from two-element lists
        ;; rather than pairs, so this does not iterpret proper alists.
        (cadr binding)
        default)))
