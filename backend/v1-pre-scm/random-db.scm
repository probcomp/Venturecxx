(declare (usual-integrations))

;; TODO First writing a version that just forward simulates to make
;; sure the rest works.
(define-structure (rdb (safe-accessors #t))
  parent
  addresses
  values)

(define (rdb-trace-search trace addr win lose)
  (if (rdb? trace)
      (rdb-trace-search-one trace addr win
       (lambda () (trace-search (trace-parent trace) addr win lose)))
      (lose)))

(define (rdb-trace-search-one trace addr win lose)
  (let loop ((as (trace-addresses trace))
             (vs (trace-values trace)))
    (cond ((null? as)
           (lose))
          ((eq? (car as) addr)
           (win (car vs)))
          (else (loop (cdr as) (cdr vs))))))

(define (rdb-trace-store! trace addr val)
  (set-trace-addresses! trace (cons addr (trace-addresses trace)))
  (set-trace-values! trace (cons val (trace-values trace))))

(define (rdb-record! trace exp env addr read-traces answer)
  (rdb-trace-store! trace addr answer))

(define (rdb-extend trace)
  (make-rdb trace '() '()))

(define (rdb-empty)
  (make-rdb #f '() '()))
