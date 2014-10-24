(declare (usual-integrations apply eval))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

(define has-assessor? (has-annotation? assessor-tag))
(define assessor-of (annotation-of assessor-tag))

(define-structure (rdb (safe-accessors #t))
  parent
  addresses
  records ; list of (exp env addr read-traces answer)
  record-map ; wt-tree mapping addresses to records
  ;; The info in addresses and records is duplicated because the
  ;; former two fields preserve insertion order, which I rely on in
  ;; rebuild-rdb.
  constraints ; wt-tree mapping addresses to values
  eval-hook)

(define (rdb-trace-search trace addr win lose)
  (if (rdb? trace)
      (rdb-trace-search-one trace addr win
       (lambda () (trace-search (rdb-parent trace) addr win lose)))
      (lose)))

(define (rdb-trace-search-one-record trace addr win lose)
  (search-wt-tree (rdb-record-map trace) addr win lose))

(define (rdb-trace-search-one trace addr win lose)
  (rdb-trace-search-one-record trace addr (lambda (rec) (win (car (cddddr rec)))) lose))

(define (rdb-trace-store! trace addr thing)
  (set-rdb-addresses! trace (cons addr (rdb-addresses trace)))
  (set-rdb-records! trace (cons thing (rdb-records trace)))
  (set-rdb-record-map! trace (wt-tree/add (rdb-record-map trace) addr thing)))

(define (rdb-trace-eval! trace exp env addr read-traces continue)
  (let ((real-answer
         (aif (rdb-eval-hook trace)
              (it exp env addr read-traces continue)
              (continue))))
    (rdb-trace-store! trace addr (list exp env addr read-traces real-answer))
    real-answer))

(define (rdb-trace-apply! trace oper opand-addrs addr read-traces continue)
  (continue))

(define (rdb-record-constraint! trace addr value)
  (set-rdb-constraints! trace (wt-tree/add (rdb-constraints trace) addr value)))

(define (rdb-extend trace)
  (make-rdb trace '() '() (make-address-wt-tree) (make-address-wt-tree) #f))

(define (rdb-empty) (rdb-extend #f))

;;; Translation of the Lightweight MCMC algorithm to the present context

(define (weight-at addr trace read-traces)
  (ensure address? addr)
  (rdb-trace-search-one-record trace addr
   (lambda (rec)
     (weight-for-at (car (cddddr rec)) addr (car rec) trace read-traces))
   (lambda () (error "Trying to compute weight for a value that isn't there" addr))))

(define (weight-for-at val addr exp trace read-traces)
  (ensure address? addr)
  ;; Expect exp to be an application
  ;; Do not look for it in the trace itself because it may not have been recorded yet.
  (let* ((subaddrs (map (lambda (i)
                          (extend-address addr `(app-sub ,i)))
                        (iota (length exp))))
         (sub-vals (map (lambda (a)
                          (traces-lookup (cons trace read-traces) a))
                        subaddrs)))
    (if (not (annotated? (car sub-vals)))
        (error "What!?"))
    (if (not (has-assessor? (car sub-vals)))
        (error "What?!?"))
    ;; Apply the assessor, but do not record it in the same trace.
    ;; I need to bind the value to an address, for uniformity
    (let* ((val-addr (extend-address addr 'value-to-assess))
           (assess-trace (store-extend trace)))
      (eval `(quote ,val) #f assess-trace val-addr '()) ; Put the value in as a constant
      (apply (assessor-of (car sub-vals)) (cons val-addr (cdr subaddrs))
             (extend-address addr 'assessment)
             assess-trace read-traces))))

(define (compatible-operators-for? addr new-trace old-trace)
  ;; Could generalize to admit different addresses in the two traces
  (ensure address? addr)
  (let ((op-addr (extend-address addr '(app-sub 0))))
    (rdb-trace-search-one
     new-trace op-addr
     (lambda (new-op)
       (rdb-trace-search-one
        old-trace op-addr
        (lambda (old-op)
          ;; Well, actually, they need only be assessed against the
          ;; same base measure (which I could perhaps detect with an
          ;; additional annotation (in fact, the base measure objects
          ;; could be opaque, since I only want to compare their
          ;; identities)) and with normalization constants with known
          ;; difference.  The latter will automatically hold of
          ;; procedures (e.g., primitives) whose assessors are
          ;; normalized.
          ;; - Being able to switch operators could even be useful,
          ;;   e.g. for clustering against clusters of variable shapes.
          (and (eqv? new-op old-op)
               (has-assessor? new-op)))
        (lambda () #f)))
     (lambda () #f))))

;; The type of the proposal is
;;   (exp env addr new-trace orig-trace read-traces resimulation-answer) -> (value weight)
;; Rebuild-rdb will return a trace built with the supplied values,
;; together with the sum of the given weights.

;; For a Metropolis-Hastings proposal, the weight has to be
;;   (assess new-value wrt resimulation in the new-trace) - (assess new-value wrt proposal distribution)
;;   - [(assess orig-value wrt resimulation in orig-trace) - (assess orig-trace wrt proposal distribution)]
;;   where the proposal distributions may be different in the two cases
;;   if they are conditioned on the current state
;; but may be computable with cancellations (e.g., for resimulation proposals)

(define (rebuild-rdb orig proposal)
  (let ((new (rdb-extend (rdb-parent orig)))
        (log-weight 0))
    (define (add-weight w)
      (set! log-weight (+ log-weight w)))
    (define (regeneration-hook exp env addr read-traces continue)
      (receive (value weight)
        (proposal exp env addr new orig read-traces continue)
        (add-weight weight)
        value))
    (set-rdb-eval-hook! new regeneration-hook)
    (for-each
     (lambda (addr record)
       ;; Order (not counting issues with coupled foreign procedures) will be
       ;; enforced by evaluation recursion regardless of the order in
       ;; which the available expressions are traversed, provided the
       ;; replacement caches results.
       ;; However, I do need to order things so that defines get executed
       ;; before lookups of those symbols.
       ;; TODO: Mutation problem: define changes the evaluation environment!
       (case* record
         ((pair exp (pair env (pair addr (pair read-traces (pair answer null)))))
          (eval exp env new addr read-traces))))
     ;; Walking over exactly the expressions already recorded is the
     ;; right thing, because it will not attempt to rerun the extend
     ;; node that contains the executing inference program itself.
     (reverse (rdb-addresses orig))
     (reverse (rdb-records orig)))
    (values new log-weight)))

;; "Minimal" in the sense that it absorbs wherever it can
;; Returns an M-H style weight
(define ((propose-minimal-resimulation-with-deterministic-overrides target replacements)
         exp env addr new orig read-traces continue)
  (ensure (or/c address? false?) target)
  (define (resampled)
    (values (continue) 0))              ; No weight
  (define (absorbed val)
    ;; Not re-executing the application expression.  Technically, the
    ;; only thing I am trying to avoid re-executing is the application
    ;; part, but I think the evaluation of the arguments gets
    ;; re-executed (in the proper order!) anyway, because they are
    ;; recorded expressions in their own right.
    (values val
            ;; TODO Could optimize this not to recompute weights if
            ;; the parameters did not change.
            (- (weight-for-at val addr exp new read-traces)
               (weight-at addr orig read-traces))))
  (if (eq? addr target)
      (resampled) ; The point was to resimulate the target address
      ;; Assume that replacements are added judiciously, namely to
      ;; random choices from the original trace (whose operators
      ;; didn't change due to other replacements?)
      (search-wt-tree replacements addr
        (lambda (it)
          (if (random-choice? addr new)
              (absorbed it)
              (error "Trying to replace the value of a deterministic computation")))
        (lambda ()
          (if (compatible-operators-for? addr new orig)
              ;; One?  Should be one...
              (rdb-trace-search-one orig addr absorbed resampled)
              (resampled)))))
  ;; TODO I believe the fresh and stale log likelihoods
  ;; mentioned in Wingate, Stuhlmuller, Goodman 2008 are
  ;; actually a distraction, in that they always cancel against
  ;; the log likelihood of newly sampled randomness.
  )

;; "Maximal" in the sense that it absorbs only when it must.  Returns
;; the density of the new trace, without subtracting off the density
;; of the old trace.  This is suitable for rejection sampling.
(define ((propose-maximal-resimulation-with-deterministic-overrides replacements)
         exp env addr new orig read-traces continue)
  (define (resampled)
    (values (continue) 0)) ; No weight
  (define (absorbed val)
    (values val (weight-for-at val addr exp new read-traces)))
  ;; Assume that replacements are added judiciously, namely to
  ;; random choices from the original trace (whose operators
  ;; didn't change due to other replacements?)
  (search-wt-tree replacements addr
    (lambda (it)
      (if (random-choice? addr new)
          (absorbed it)
          (error "Trying to replace the value of a deterministic computation")))
    resampled))

(define (random-choice? addr trace)
  ;; Ignores possibility of constraints induced by observations (for
  ;; that, use unconstrained-random-choice?).
  ;; TODO allow assessable procedures from contextual traces?
  (rdb-trace-search-one
   trace (extend-address addr '(app-sub 0))
   has-assessor?
   (lambda () #f)))

(define (unconstrained-random-choice? addr trace)
  (and (random-choice? addr trace)
       (not (wt-tree/member? addr (rdb-constraints trace)))))

(define (random-choices trace)
  (filter (lambda (a) (unconstrained-random-choice? a trace)) (rdb-addresses trace)))

(define (select-uniformly items)
  (let ((index (random (length items))))
    (list-ref items index)))

(define (prior-resimulate addr trace)
  (rdb-trace-search-one-record
   trace addr
   (lambda (rec)
     (let ((exp (car rec)) (env (cadr rec)) (addr (caddr rec)) (read-traces (cadddr rec)))
       ;; do-eval here circumvents the trace recording machinery (both
       ;; read and write)
       (do-eval exp env trace addr read-traces)))
   (lambda () (error "What?"))))

(define (rdb-trace-commit! from to)
  (set-rdb-addresses! to (rdb-addresses from))
  (set-rdb-records! to (rdb-records from))
  (set-rdb-record-map! to (rdb-record-map from)))
