;;; Copyright (c) 2014 MIT Probabilistic Computing Project.
;;;
;;; This file is part of Venture.
;;;
;;; Venture is free software: you can redistribute it and/or modify
;;; it under the terms of the GNU General Public License as published by
;;; the Free Software Foundation, either version 3 of the License, or
;;; (at your option) any later version.
;;;
;;; Venture is distributed in the hope that it will be useful,
;;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;;; GNU General Public License for more details.
;;;
;;; You should have received a copy of the GNU General Public License
;;; along with Venture.  If not, see <http://www.gnu.org/licenses/>.

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
  (gnuplot-multiple (list (apply gnuplot-alist-plot alist adverbs))))

(define (gnuplot-alist-plot alist . adverbs)
  (let ((gnuplot-extra (lax-alist-lookup adverbs 'commanding ""))
        (gnuplot-prefix (lax-alist-lookup adverbs 'prefixing "")))
    (make-gnu-plot
     alist
     (string-append
      "set style data lines; "
      "set key noautotitles; "
      gnuplot-prefix)
     gnuplot-extra)))

(define (gnuplot-histogram-alist alist #!optional data-name binsize)
  (gnuplot-multiple (list (gnuplot-histogram-alist-plot alist data-name binsize))))

(define (gnuplot-histogram-alist-plot alist #!optional data-name binsize)
  ;; TODO Abstract the commonalities among these two
  (define (compute-bin-size numbers)
    (let* ((sorted (sort numbers <))
           (minimum (car sorted))
           (maximum (last sorted)))
      (/ (- maximum minimum) 200)))
  (if (default-object? binsize)
      (set! binsize (compute-bin-size (map car alist))))
  (make-gnu-plot
   alist
   (string-append
    "binwidth=" (number->string binsize) "; "
    "bin(x,width)=width*floor(x/width)+width/2; "
    "set boxwidth binwidth; "
    "set style fill solid; ")
   (string-append
    "using (bin($1,binwidth)):($2/binwidth) smooth freq with boxes "
    (if (default-object? data-name) "" (string-append "title \"" data-name "\" ")))))

;; A "lax alist" is a list whose pairs are treated as alist elements,
;; but which is allowed to have non-pairs also (which are ignored).
(define (lax-alist-lookup alist item default #!optional =)
  (let ((binding (assoc item (filter pair? alist) =)))
    (if binding
        ;; I really want to be looking up from two-element lists
        ;; rather than pairs, so this does not iterpret proper alists.
        (cadr binding)
        default)))

(define (gnuplot-direct-to-file filename)
  (make-gnu-plot #f (string-append "set term png; set output \"" filename "\"") #f))

(define-structure (gnu-plot (safe-accessors #t))
  data
  prefix
  control)

(define (gnuplot-multiple plots)
  (let loop ((plots plots)
             (prefixes '())
             (plot-lines '()))
    (cond ((null? plots)
           (let ((command (string-append
                           "gnuplot -p -e \'"
                           (apply string-append (reverse prefixes))
                           "plot " (apply string-append (reverse plot-lines))
                           "'")))
             (display command)
             (newline)
             (run-shell-command command)))
          ((pair? plots)
           (let ((data (gnu-plot-data (car plots)))
                 (prefix (gnu-plot-prefix (car plots)))
                 (control (gnu-plot-control (car plots)))
                 (control-separator (if (null? (cdr plots)) "" ", ")))
             (if data
                 (call-with-temporary-file-pathname
                  (lambda (pathname)
                    (gnuplot-write-alist data pathname)
                    (loop (cdr plots)
                          (cons (string-append prefix "; ") prefixes)
                          (cons (string-append "\"" (->namestring pathname) "\" " control control-separator) plot-lines))))
                 (loop (cdr plots)
                       (cons (string-append (gnu-plot-prefix (car plots)) "; ") prefixes)
                       plot-lines)))))))
