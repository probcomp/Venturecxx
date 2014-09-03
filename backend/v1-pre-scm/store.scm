(declare (usual-integrations))

;;; A minimal "trace" that just stores the values and does not allow
;;; re-execution.

(define-structure (store (safe-accessors #t))
  parent
  addresses
  values)

;; TODO Make parent fetching generic, and implement trace-search
;; uniformly over all trace types
(define (store-trace-search trace addr win lose)
  (if (store? trace)
      (store-trace-search-one trace addr win
       (lambda () (trace-search (store-parent trace) addr win lose)))
      (lose)))

(define (store-trace-search-one trace addr win lose)
  (search-parallel-lists
   addr (store-addresses trace) (store-values trace) win lose))

(define (store-record! trace exp env addr read-traces answer)
  (set-store-addresses! trace (cons addr (store-addresses trace)))
  (set-store-values! trace (cons answer (store-values trace)))
  answer)

(define (store-record-constraint! trace addr value)
  (error "Forward execution does not support constraining; did you mean to use mutation?" trace addr value))

(define (store-extend trace)
  (make-store trace '() '()))
