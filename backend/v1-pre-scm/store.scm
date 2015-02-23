(declare (usual-integrations))

;;; A minimal "trace" that just stores the values and does not allow
;;; re-execution.

(define-structure (store (safe-accessors #t))
  parent
  values ; wt-tree mapping addresses to values
  )

;; TODO Make parent fetching generic, and implement trace-search
;; uniformly over all trace types
(define (store-trace-search trace addr win lose)
  (if (store? trace)
      (store-trace-search-one trace addr win
       (lambda () (trace-search (store-parent trace) addr win lose)))
      (lose)))

(define (store-trace-search-one trace addr win lose)
  (search-wt-tree (store-values trace) addr win lose))

(define (store-trace-eval! trace exp env addr read-traces continue)
  (let ((answer (continue)))
    (set-store-values! trace (wt-tree/add (store-values trace) addr answer))
    answer))

(define (store-trace-apply! trace oper opand-addrs addr read-traces continue)
  (continue))

(define (store-record-constraint! trace addr value)
  (error "Forward execution does not support constraining; did you mean to use mutation?" trace addr value))

(define (store-extend trace)
  (make-store trace (make-address-wt-tree)))
