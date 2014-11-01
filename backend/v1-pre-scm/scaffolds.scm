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
      ;; No weight, because assessment of new value cancels against
      ;; the probability of proposing it
      ;; - since we are proposing from the prior
      (values (continue) 0)) ; No weight
    (define (propose-base)
      (if (default-object? propose)
          (resampled)
          (propose exp env addr new read-traces continue)))
    (define (proposed)
      (if (default-object? compute)
          (propose-base)
          (receive (answer weight)
            (propose-base)
            (values answer (cons weight (compute exp env addr new read-traces (make-resimulated answer)))))))
    (define (unchanged val)
      (let ((commit-state (simulation-effect-at val addr exp new read-traces continue)))
        (if (default-object? compute)
            (begin
              (commit-state)
              (values val 0))
            (let ((computed (compute exp env addr new read-traces (make-unchanged val))))
              (commit-state)
              (values val (cons 0 computed))))))
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
            (let ((computed (compute exp env addr new read-traces (make-absorbed val weight))))
              (commit-state)
              (values val (cons weight computed))))))
    (scaffold exp env addr new read-traces proposed absorbed unchanged))
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
  (define (former-weight exp env addr new read-traces answer)
    (if (or (resimulated? answer) (unchanged? answer))
        ;; No weight, because assessment of old value cancels against
        ;; the probability of proposing it back
        ;; - since we are proposing from the prior, AND
        ;; - all the arguments are the same because the target is unique
        0
        (- (weight-at addr trace))))
  (receive (new-trace weight+former-weight)
    (regen/copy trace scaffold #!default former-weight + 0)
    (values new-trace (cdr weight+former-weight))))

(define-structure (unchanged (safe-accessors #t)) value)
(define-structure (resimulated (safe-accessors #t)) value)
(define-structure (absorbed (safe-accessors #t)) value weight)

;; "Maximal" in the sense that it absorbs only when it must.
(define ((maximal-resimulation-scaffold/deterministic-overrides replacements)
         exp env addr trace read-traces resampled absorbed unchanged)
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
;; "unchanged", so a future detach that paid attention to that would
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
      ;; TODO Do I need to be sure to call continue from absorbing here?
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
    (lambda (exp env addr trace read-traces resampled absorbed unchanged)
      (search-wt-tree statuses addr
        (lambda (it)
          (cond ((resimulated? it)
                 (resampled))
                ((absorbed? it)
                 (absorbed (absorbed-value it)))
                (error "Unknown status" it)))
        ;; New node
        resampled))))

;; "Minimal resimulation" in the sense that it absorbs wherever it can.
;; "Minimal reexecution" in the sense that it mark "unchanged" any nodes
;; it can, so a future detach that paid attention to that would
;; unincorporate as little as possible.
(define (minimal-resimulation-minimal-reexecution-scaffold/one-target+deterministic-overrides trace target replacements)
  (ensure (or/c address? false?) target)
  (let ((statuses (make-wt-tree address-wt-tree-type)))
    (define (proposal exp env addr new orig read-traces continue)
      (define old-val
        (rdb-trace-search-one orig addr (lambda (v) v)
          (lambda ()
            (error "This should never happen if values are being replayed properly"))))
      (define resim-tag (make-resimulated #f))
      (define (resampled)
        (set! statuses (wt-tree/add statuses addr resim-tag))
        (values old-val 0))
      (define (unchanged)
        ;; TODO This is ok for primitive unchanged procedures, except
        ;; that I actually want to rerun their side-effects, if any,
        ;; to make more sure that the new trace follows the same
        ;; control trajectory as the old.
        (set! statuses (wt-tree/add statuses addr (make-unchanged old-val)))
        (values old-val 0))
      (define (absorbed)
        (set! statuses (wt-tree/add statuses addr (make-absorbed val #f)))
        ;; TODO Ditto about rerunning side-effects
        (values old-val 0))
      (define (propagate-status addr*)
        (let ((parent-status (wt-tree/lookup statuses addr* #f)))
          (cond ((unchanged? parent-status)
                 (unchanged))
                ((resimulated? parent-status)
                 (resampled))
                ((absorbed? parent-status)
                 (unchanged))
                (else (error "What!?")))))
      (if (eq? addr target)
          (begin
            (continue)
            (resampled)) ; The point was to resimulate the target address
          ;; ASSUME that replacements are added judiciously, namely to
          ;; random choices from the original trace (whose operators
          ;; didn't change due to other replacements?)
          (search-wt-tree replacements addr
            (lambda (it)
              (if (random-choice? addr new)
                  (absorbed)
                  (error "Trying to replace the value of a deterministic computation")))
            (lambda ()
              (rdb-trace-search-one-record orig addr
                (lambda-case*
                 ((evaluation-record exp env _ read-traces answer)
                  (case* exp
                    ((constant _) ;; Don't need to continue
                     (unchanged))
                    ((var x) ;; Don't need to continue
                     (env-search env x
                       (lambda (addr*)
                         ;; TODO What about values that come in from enclosing traces?
                         (propagate-status addr*))
                       (lambda ()
                         ;; Assume Scheme value, which are taken to be constant
                         (unchanged))))
                    ((lambda-form _ _)
                     ;; In the sense of the body of the operator, lambda forms are constant.
                     ;; That sense is not actually very good for annotated compound procedures,
                     ;; because most everything else tends to treat them as primitive.
                     ;; I think I want the generated rather than old
                     ;; value, to make sure the right things end up in
                     ;; the closure (though, they should all be
                     ;; addresses anyway, right?)
                     (let ((val (continue)))
                       (set! statuses (wt-tree/add statuses addr (make-unchanged val)))
                       (values val 0)))
                    ((trace-in-form _ _)
                     ;; Trying to track dependencies through a
                     ;; trace-in form was what got me confused last
                     ;; time.
                     (begin (continue) (resampled)))
                    ((definition _ _)
                     ;; The value of the definition is still "I defined something"
                     (begin (continue) (unchanged)))
                    ((if-form _ _ _)
                     (let ((predicate-status (wt-tree/lookup statuses (extend-address addr 'if-p) #f)))
                       (continue)
                       (cond ((or (unchanged? predicate-status) (absorbed? predicate-status))
                              (let ((p-val (rdb-trace-search-one orig (extend-address addr 'if-p) (lambda (v) v) (lambda () (error "What !?")))))
                                (propagate-status (extend-address addr (if p-val 'if-c 'if-a)))))
                             ((resimulated? predicate-status)
                              ;; Brush
                              ;; TODO Mark the enclosed nodes as brush, e.g. with a fluid let?
                              (resampled)) ; Brush is always resampled; the output of the if propagates that
                             (else (error "What!??")))))
                    ((begin-form forms)
                     (begin
                       (continue)
                       (propagate-status (extend-address addr `(begin ,(- (length forms) 1))))))
                    ((operative-form operative subforms)
                     ;; TODO Most of the operatives are macros, which
                     ;; might as well be macro-expanded before they
                     ;; are ever even traced.  The other currently
                     ;; extant operatives are constant (under
                     ;; inference).
                     (begin
                       (continue)
                       (unchanged)))
                    (_ ;; Application
                     (let* ((substati (map (lambda (i)
                                             (wt-tree/lookup statuses (extend-address addr `(app-sub ,i))))
                                           (iota (length exp))))
                            (operator-status (car substati))
                            (operand-stati (cdr substati))
                            (args-fixed? (every (lambda (s) (or (unchanged? s) (absorbed? s))) operand-stati)))
                       (cond ((or (unchanged? operator-status) (absorbed? operator-status))
                              (let ((operator (rdb-trace-search-one orig (extend-address addr '(app-sub 0)) (lambda (v) v) (lambda () (error "What??")))))
                                (cond ((or (has-assessor? operator) (has-coupled-assessor? operator))
                                       ;; CONSIDER There may be a bug
                                       ;; with suppressing recursion
                                       ;; inside an assessable
                                       ;; compound here, where the
                                       ;; internal nodes later get
                                       ;; mistaken for new or brush.
                                       (if args-fixed?
                                           (unchanged)
                                           ;; Assume the assessor can absorb changes in any input
                                           (absorbed)))
                                      ((compound? (annotated-base* operator))
                                       ;; The recursive call(s) will take care of it
                                       (continue)
                                       (propagate-status (extend-address addr 'app)))
                                      ;; TODO A case for things annotated with incorporators but not assessors?
                                      (else (if args-fixed? (unchanged) (resampled))))))
                             ((resimulated? operator-status)
                              ;; Brush
                              ;; TODO Mark the enclosed nodes as brush
                              ;; (but not the nodes of evaluating the
                              ;; arguments), e.g. with a fluid let?
                              (continue)
                              (resampled) ; Brush is always resampled; the output of the application propagates that
                             (else (error "What??"))))))))
                 (_ (error "What?!?")))
                (lambda ()
                  (error "This should never happen if values are being replayed properly")))))))
    (rebuild-rdb trace proposal)
    (lambda (exp env addr trace read-traces resampled absorbed unchanged)
      (search-wt-tree statuses addr
        (lambda (it)
          (cond ((resimulated? it)
                 (resampled))
                ((absorbed? it)
                 (absorbed (absorbed-value it)))
                ((unchanged? it)
                 (unchanged (unchanged-value it)))
                (error "Unknown status" it)))
        ;; New node
        resampled))))
