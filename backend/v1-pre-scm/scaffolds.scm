(declare (usual-integrations))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

(define (regen/copy trace scaffold #!optional compute combine init)
  (rebuild-rdb trace (scaffold compute)
    (if (default-object? combine)
        #!default
        (lambda (increment total)
          (cons (+ (car increment) (car total))
                (combine (cdr increment) (cdr total)))))
    (if (default-object? init)
        #!default
        (cons 0 init))))

;; Here's a way to make a detach that
;; - Does not produce a trace with a hole in it, as such,
;; - Returns the proper detach weight, and
;; - If instrumented, would be noticed to evaluate incorporators in
;;   regen order, not reverse regen order.
(define (detach/copy trace scaffold)
  (define (former-weight exp env addr new orig read-traces answer)
    (if (resimulated? answer)
        0
        (- (weight-at addr orig))))
  (receive (new-trace weight+former-weight)
    (regen/copy trace scaffold former-weight + 0)
    (values new-trace (cdr weight+former-weight))))

(define-structure (resimulated (safe-accessors #t)) value)
(define-structure (absorbed (safe-accessors #t)) value weight)

;; "Minimal" in the sense that it absorbs wherever it can
;; Returns an M-H style weight
(define (((minimal-resimulation-scaffold/one-target+deterministic-overrides target replacements)
          #!optional compute)
         exp env addr new orig read-traces continue)
  (ensure (or/c address? false?) target)
  (define (resampled)
    (if (default-object? compute)
        (values (continue) 0)            ; No weight
        (let ((answer (continue)))
          (values answer (cons 0 (compute exp env addr new orig read-traces (make-resimulated answer)))))))
  (define (absorbed val)
    ;; Not re-executing the application expression.  Technically, the
    ;; only thing I am trying to avoid re-executing is the application
    ;; part, but I ASSUME the evaluation of the arguments gets
    ;; re-executed (in the proper order!) anyway, because they are
    ;; recorded expressions in their own right.
    (receive (weight commit-state)
      (assessment+effect-at val addr exp new read-traces)
      (if (default-object? compute)
          (begin
            (commit-state)
            (values val weight))
          (let ((computed (compute exp env addr new orig read-traces (make-absorbed val weight))))
            (commit-state)
            (values val (cons weight computed))))))
  (if (eq? addr target)
      (resampled) ; The point was to resimulate the target address
      ;; ASSUME that replacements are added judiciously, namely to
      ;; random choices from the original trace (whose operators
      ;; didn't change due to other replacements?)
      (search-wt-tree replacements addr
        (lambda (it)
          (if (random-choice? addr new)
              (absorbed it)
              (error "Trying to replace the value of a deterministic computation")))
        (lambda ()
          ;; TODO Could optimize (including reducing scaffold size
          ;; further) if the parameters did not change.
          (if (compatible-operators-for? addr new orig)
              ;; One?  Should be one...
              (rdb-trace-search-one orig addr absorbed resampled)
              (resampled)))))
  ;; CONSIDER I believe the fresh and stale log likelihoods
  ;; mentioned in Wingate, Stuhlmuller, Goodman 2008 are
  ;; actually a distraction, in that they always cancel against
  ;; the log likelihood of newly sampled randomness.
  )

;; "Maximal" in the sense that it absorbs only when it must.  Returns
;; the density of the new trace, without subtracting off the density
;; of the old trace.  This is suitable for rejection sampling once the
;; bound has been computed.

;; If the optional compute argument is supplied, calls it at every
;; node and returns the pair of the density in the new trace with the
;; result of compute.  With an appropriate choice of the compute
;; function (and corresponding accumulator for rebuild-rdb), this
;; facility can be useful for computing the bound for rejection.
(define (((maximal-resimulation-scaffold/deterministic-overrides replacements)
          #!optional compute)
         exp env addr new orig read-traces continue)
  (define (resampled)
    (if (default-object? compute)
        (values (continue) 0)            ; No weight
        (let ((answer (continue)))
          (values answer (cons 0 (compute exp env addr new orig read-traces (make-resimulated answer)))))))
  (define (absorbed val)
    (receive (weight commit-state)
      (assessment+effect-at val addr exp new read-traces)
      (if (default-object? compute)
          (begin
            (commit-state)
            (values val weight))
          (let ((computed (compute exp env addr new orig read-traces (make-absorbed val weight))))
            (commit-state)
            (values val (cons weight computed))))))
  ;; ASSUME that replacements are added judiciously, namely to
  ;; random choices from the original trace (whose operators
  ;; didn't change due to other replacements?)
  (search-wt-tree replacements addr
    (lambda (it)
      (if (random-choice? addr new)
          (absorbed it)
          (error "Trying to replace the value of a deterministic computation")))
    resampled))

