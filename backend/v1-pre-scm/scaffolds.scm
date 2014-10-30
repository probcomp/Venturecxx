(declare (usual-integrations))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

;; Returns a proposed trace and the importance weight of proposing
;; that trace vs the local posterior on the subproblem defined by the
;; scaffold.

;; If the optional propose argument is supplied, it is called for
;; every node whose value is to change, and is to return a new value
;; and a weight for that value.  The weight returned by regen is the
;; sum of the weights returned by propose, together with the
;; importance weights computed at the absorbing nodes.  If each call
;; to propose returns the importance weight of the value it returns
;; against the prior at that node, then that sum will be the
;; importance weight of proposing the trace regen returns against the
;; local posterior on the subproblem defined by the scaffold.

;; If the optional compute, combine, and init arguments are supplied,
;; calls the given compute function on every traversed node, and also
;; returns the result of accumulating the values returned thereby with
;; combine, starting from init.
(define (regen/copy trace scaffold #!optional propose compute combine init)
  (define (proposal exp env addr new orig read-traces continue)
    (define (resampled)
      (values (continue) 0)) ; No weight
    (define (propose-base)
      (if (default-object? propose)
          (resampled)
          (propose exp env addr new orig read-traces continue)))
    (define (proposed)
      (if (default-object? compute)
          (propose-base)
          (receive (answer weight)
            (propose-base)
            (values answer (cons weight (compute exp env addr new orig read-traces (make-resimulated answer)))))))
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
    (scaffold exp env addr new read-traces proposed absorbed))
  (rebuild-rdb trace proposal
    (if (default-object? combine)
        #!default
        (lambda (increment total)
          (cons (+ (car increment) (car total))
                (combine (cdr increment) (cdr total)))))
    (if (default-object? init)
        #!default
        (cons 0 init)))
  ;; CONSIDER I believe the fresh and stale log likelihoods
  ;; mentioned in Wingate, Stuhlmuller, Goodman 2008 are
  ;; actually a distraction, in that they always cancel against
  ;; the log likelihood of newly sampled randomness.
  )

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
    (regen/copy trace scaffold #!default former-weight + 0)
    (values new-trace (cdr weight+former-weight))))

(define-structure (resimulated (safe-accessors #t)) value)
(define-structure (absorbed (safe-accessors #t)) value weight)

;; "Maximal" in the sense that it absorbs only when it must.
(define ((maximal-resimulation-scaffold/deterministic-overrides replacements)
         exp env addr trace read-traces resampled absorbed)
  ;; ASSUME that replacements are added judiciously, namely to
  ;; random choices from the original trace (whose operators
  ;; didn't change due to other replacements?)
  (search-wt-tree replacements addr
    (lambda (it)
      (if (random-choice? addr trace)
          (absorbed it)
          (error "Trying to replace the value of a deterministic computation")))
    resampled))

;; "Minimal resimulation" in the sense that it absorbs wherever it can.
;; "Maximal reexecution" in the sense that it does not mark any nodes
;; "ignored", so a future detach that paid attention to that would
;; unincorporate everything.
(define (minimal-resimulation-maximal-reexecution-scaffold/one-target+deterministic-overrides trace target replacements)
  (ensure (or/c address? false?) target)
  (let ((statuses (make-wt-tree address-wt-tree-type)))
    (define (proposal exp env addr new orig read-traces continue)
      (define resim-tag (make-resimulated #f))
      (define (resampled)
        (set! statuses (wt-tree/add statuses addr resim-tag))
        ;; TODO: To re-trace the execution history properly, this
        ;; needs to be the old value.  However, right now the only
        ;; effect of getting it wrong can be mistaking some new or
        ;; brush nodes for resimulated nodes and vice versa, which is
        ;; a non-issue because they are both resimulated anyway.
        (values (continue) 0))
      (define (absorbed val)
        (set! statuses (wt-tree/add statuses addr (make-absorbed val #f)))
        (values val 0))
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
                  (resampled))))))
    (rebuild-rdb trace proposal)
    (lambda (exp env addr trace read-traces resampled absorbed)
      (search-wt-tree statuses addr
        (lambda (it)
          (cond ((resimulated? it)
                 (resampled))
                ((absorbed? it)
                 (absorbed (absorbed-value it)))
                (error "Unknown status" it)))
        ;; New node
        resampled))))
