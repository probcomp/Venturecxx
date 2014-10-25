(declare (usual-integrations apply eval))
(declare (integrate-external "syntax"))
(declare (integrate-external "v1-pre"))
(declare (integrate-external "pattern-case/pattern-case"))

;;; Assessors for SPs that have internal state

;; The interface for assessing simulators that mutate state (and whose
;; applications are therefore coupled) is to annotate them with a
;; coupled-assessor record at the coupled-assessor-tag.  This record
;; has three fields:
;; - get, which is a nullary procedure that reads the state
;; - set, which is a unary procedure that writes the state
;; - assess, which is a (pure) procedure of type
;;     a -> b -> x1 -> ... -> xn -> (Assessment, b)
;;   for a simulator of type
;;     x1 -> ... -> xn -> Random a
;;   that contains an internal state of type b whose changes are
;;   deterministically determined by the inputs and the chosen output a.

(define coupled-assessor-tag (make-annotation-tag))
(define-integrable has-coupled-assessor? (has-annotation? coupled-assessor-tag))
(define-integrable coupled-assessor-of (annotation-of coupled-assessor-tag))

(define-structure (coupled-assessor (safe-accessors #t))
  get
  set
  assess)
(define-algebraic-matcher coupled-assessor coupled-assessor? coupled-assessor-get coupled-assessor-set coupled-assessor-assess)

;;; RandomDB representation

(define-structure (evaluation-record (safe-accessors #t))
  exp
  env
  addr
  read-traces
  answer)
(define-algebraic-matcher evaluation-record evaluation-record? evaluation-record-exp evaluation-record-env evaluation-record-addr evaluation-record-read-traces evaluation-record-answer)

(define-structure (rdb (safe-accessors #t))
  parent
  addresses
  records ; list of evaluation-records
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
  (rdb-trace-search-one-record trace addr (lambda (rec) (win (evaluation-record-answer rec))) lose))

(define (rdb-trace-store! trace addr thing)
  (set-rdb-addresses! trace (cons addr (rdb-addresses trace)))
  (set-rdb-records! trace (cons thing (rdb-records trace)))
  (set-rdb-record-map! trace (wt-tree/add (rdb-record-map trace) addr thing)))

(define (rdb-trace-eval! trace exp env addr read-traces continue)
  (let ((real-answer
         (aif (rdb-eval-hook trace)
              (it exp env addr read-traces continue)
              (continue))))
    (rdb-trace-store! trace addr (make-evaluation-record exp env addr read-traces real-answer))
    real-answer))

(define (rdb-trace-apply! trace oper opand-addrs addr read-traces continue)
  (continue))

(define (rdb-record-constraint! trace addr value)
  (set-rdb-constraints! trace (wt-tree/add (rdb-constraints trace) addr value)))

(define (rdb-extend trace)
  (make-rdb trace '() '() (make-address-wt-tree) (make-address-wt-tree) #f))

(define (rdb-empty) (rdb-extend #f))

;;; Translation of the Lightweight MCMC algorithm to the present context

(define (weight-at addr trace)
  (ensure address? addr)
  (rdb-trace-search-one-record trace addr
   (lambda (rec)
     (case* rec
       ((evaluation-record exp _ _ read-traces answer)
        (receive (weight commit-state)
          (assessment+effect-at answer addr exp trace read-traces)
          weight))))
   (lambda () (error "Trying to compute weight for a value that isn't there" addr))))

(define (assessment+effect-at val addr exp trace read-traces)
  (ensure address? addr)
  ;; Expect exp to be an application
  ;; Do not look for it in the trace itself because it may not have been recorded yet.
  (let* ((subaddrs (map (lambda (i)
                          (extend-address addr `(app-sub ,i)))
                        (iota (length exp))))
         (operator (traces-lookup (cons trace read-traces) (car subaddrs))))
    (if (not (annotated? operator))
        (error "What!?"))
    (cond ((has-assessor? operator)
           (do-assess (assessor-of operator) val subaddrs addr trace read-traces))
          ((has-coupled-assessor? operator)
           (do-coupled-assess (coupled-assessor-of operator) val subaddrs addr trace read-traces))
          (else
           (error "What?!?")))))

(define (do-assess assessor val subaddrs addr trace read-traces)
  (values
   (apply-in-void-subtrace
    assessor (list val) (cdr subaddrs) addr trace read-traces)
   (lambda () 'ok)))

(define (do-coupled-assess op-coupled-assessor val subaddrs addr trace read-traces)
  (case* (annotated-base op-coupled-assessor)
    ((coupled-assessor get set assess)
     (let ((cur-state (apply-in-void-subtrace get '() '() addr trace read-traces)))
       (case* (apply-in-void-subtrace
               assess (list val cur-state) (cdr subaddrs)
               addr trace read-traces)
         ((pair assessment new-state)
          (values assessment
            (lambda ()
              (apply-in-void-subtrace set (list new-state) '() addr trace read-traces)))))))))

(define (same-operators? new-op old-op)
  (case* (cons new-op old-op)
    ((pair (annotated new-base _)
           (annotated old-base _))
     ;; TODO Compare metadata?
     (same-operators? new-base old-base))
    ((pair (compound new-formals new-body new-env new-trace new-read-traces)
           (compound old-formals old-body old-env old-trace old-read-traces))
     ;; TODO Is this coarse enough?
     (and (eqv? new-formals old-formals)
          (eqv? new-body old-body)
          (eqv? new-env old-env)
          ; (eqv? new-trace old-trace) ; Might want to check compatibility of closed values, but the actual trace objects are different, of course.
          (equal? new-read-traces old-read-traces)))
    ((pair (foreign new-sim)
           (foreign old-sim))
     ;; One might think this would not work for foreign procedures
     ;; generated dynamically by scheme-procedure-on-foo->v1-foreign,
     ;; and one would be right; but those aren't assessable anyway, so
     ;; it doesn't matter.
     (eqv? new-sim old-sim))
    (_  #f)))

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
          (and (same-operators? new-op old-op)
               (has-assessor? new-op)))
        (lambda () #f)))
     (lambda () #f))))

;; The type of the proposal is
;;   (exp env addr new-trace orig-trace read-traces resimulation-answer) -> (value weight)
;; Rebuild-rdb will return a trace built with the supplied values,
;; together with the sum of the given weights.
;; The user can control the type of the data accumulated by supplying the
;; optional accum and init arguments, by analogy with fold.

;; For a Metropolis-Hastings proposal, the weight has to be
;;   (assess new-value wrt resimulation in the new-trace) - (assess new-value wrt proposal distribution)
;;   - [(assess orig-value wrt resimulation in orig-trace) - (assess orig-trace wrt proposal distribution)]
;;   where the proposal distributions may be different in the two cases
;;   if they are conditioned on the current state.
;; The weight may be computable with cancellations (e.g., for
;; resimulation proposals).

(define (rebuild-rdb orig proposal #!optional accum init)
  (if (default-object? accum)
      (set! accum +))
  (if (default-object? init)
      (set! init 0))
  (let ((new (rdb-extend (rdb-parent orig)))
        (total init))
    (define (count w)
      (set! total (accum w total)))
    (define (regeneration-hook exp env addr read-traces continue)
      (receive (value weight)
        (proposal exp env addr new orig read-traces continue)
        (count weight)
        value))
    (set-rdb-eval-hook! new regeneration-hook)
    (for-each
     (lambda (addr record)
       ;; Order (not counting issues with coupled foreign procedures) will be
       ;; enforced by evaluation recursion regardless of the order in
       ;; which the available expressions are traversed, provided the
       ;; replacement caches results.
       ;; However, I do need to order things so that defines get
       ;; executed before lookups of those symbols, because define
       ;; changes the evaluation environment.
       (case* record
         ((evaluation-record exp env addr read-traces answer)
          (eval exp env new addr read-traces))))
     ;; Walking over exactly the expressions already recorded is the
     ;; right thing, because it will not attempt to rerun the extend
     ;; node that contains the executing inference program itself.
     (reverse (rdb-addresses orig))
     (reverse (rdb-records orig)))
    (values new total)))

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
    ;; part, but I ASSUME the evaluation of the arguments gets
    ;; re-executed (in the proper order!) anyway, because they are
    ;; recorded expressions in their own right.
    (receive (new-weight commit-state)
      (assessment+effect-at val addr exp new read-traces)
      (commit-state)
      (values val
              ;; TODO Could optimize this not to recompute weights if
              ;; the parameters did not change.
              (- new-weight
                 (weight-at addr orig)))))
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
          (if (compatible-operators-for? addr new orig)
              ;; One?  Should be one...
              (rdb-trace-search-one orig addr absorbed resampled)
              (resampled)))))
  ;; CONSIDER I believe the fresh and stale log likelihoods
  ;; mentioned in Wingate, Stuhlmuller, Goodman 2008 are
  ;; actually a distraction, in that they always cancel against
  ;; the log likelihood of newly sampled randomness.
  )

(define (random-choice? addr trace)
  ;; Ignores possibility of constraints induced by observations (for
  ;; that, use unconstrained-random-choice?).

  ;; Searching one trace level is ok here because the extended address
  ;; must be in the same trace as the original.
  (rdb-trace-search-one
   trace (extend-address addr '(app-sub 0))
   (lambda (op)
     (or (has-assessor? op)
         (has-coupled-assessor? op)))
   (lambda () #f)))

(define (unconstrained-random-choice? addr trace)
  (and (random-choice? addr trace)
       (not (wt-tree/member? addr (rdb-constraints trace)))))

(define (random-choices trace)
  (filter (lambda (a) (unconstrained-random-choice? a trace)) (rdb-addresses trace)))

(define (select-uniformly items)
  (let ((index (random (length items))))
    (list-ref items index)))

(define (rdb-trace-commit! from to)
  (set-rdb-addresses! to (rdb-addresses from))
  (set-rdb-records! to (rdb-records from))
  (set-rdb-record-map! to (rdb-record-map from)))
