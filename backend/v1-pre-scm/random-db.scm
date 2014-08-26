(declare (usual-integrations))

;; TODO First writing a version that just forward simulates to make
;; sure the rest works.
(define-structure (rdb (safe-accessors #t))
  parent
  addresses
  records
  record-hook)

(define (rdb-trace-search trace addr win lose)
  (if (rdb? trace)
      (rdb-trace-search-one trace addr win
       (lambda () (trace-search (rdb-parent trace) addr win lose)))
      (lose)))

(define (rdb-trace-search-one-record trace addr win lose)
  (let loop ((as (rdb-addresses trace))
             (vs (rdb-records trace)))
    (cond ((null? as)
           (lose))
          ((eq? (car as) addr)
           (win (car vs)))
          (else (loop (cdr as) (cdr vs))))))

(define (rdb-trace-search-one trace addr win lose)
  (rdb-trace-search-one-record trace addr (lambda (rec) (win (car (cddddr rec)))) lose))

(define (rdb-trace-store! trace addr thing)
  (set-rdb-addresses! trace (cons addr (rdb-addresses trace)))
  (set-rdb-records! trace (cons thing (rdb-records trace))))

(define (rdb-record! trace exp env addr read-traces answer)
  (let ((real-answer
         (aif (rdb-record-hook trace)
              (it exp env addr read-traces answer)
              answer)))
    (rdb-trace-store! trace addr (list exp env addr read-traces real-answer))
    real-answer))

(define (rdb-extend trace)
  (make-rdb trace '() '() #f))

(define (rdb-empty)
  (make-rdb #f '() '() #f))

;;; Translation of the Lightweight MCMC algorithm to the present context

(define (weight-at addr trace read-traces)
  (rdb-trace-search-one-record trace addr
   (lambda (rec)
     (weight-for-at (car (cdddr rec)) addr (car rec) trace read-traces))
   (lambda () (error "Trying to compute weight for a value that isn't there" addr))))

(define (weight-for-at val addr exp trace read-traces)
  ;; Expect exp for be an application
  ;; Do not look for it in the trace itself because it may not have been recorded yet.
  (let ((sub-vals (map (lambda (i)
                         (traces-lookup (cons trace read-traces) (extend-address addr `(app-sub ,i))))
                       (iota (length exp)))))
    (if (not (primitive? (car sub-vals)))
        (error "What!?"))
    (if (not (primitive-log-density (car sub-vals)))
        (error "What?!?"))
    ((access apply system-global-environment)
     (primitive-log-density (car sub-vals)) val (cdr sub-vals))))

(define (compatible-operators-for? addr new-trace old-trace)
  (let ((op-addr (extend-address addr '(app-sub 0))))
    (rdb-trace-search-one
     new-trace op-addr
     (lambda (new-op)
       (rdb-trace-search-one
        old-trace op-addr
        (lambda (old-op)
          (and (eqv? new-op old-op)
               (primitive? new-op)
               (primitive-log-density new-op)))
        (lambda () #f)))
     (lambda () #f))))

(define (rebuild-rdb orig replacements)
  (pp orig)
  (let ((new (rdb-extend (rdb-parent orig)))
        (log-weight 0))
    (define (add-weight w)
      (pp w)
      (set! log-weight (+ log-weight w)))
    (define (regeneration-hook exp env addr read-traces answer)
      (pp exp)
      (define new-value)
      (define (record-as-resampled)
        (set! new-value answer)) ; No weight
      (define (record-as-absorbed val)
        (set! new-value val)
        ;; TODO Could optimize this not to recompute weights if the
        ;; parameters did not change.
        (add-weight (- (weight-for-at new-value addr exp new read-traces)
                       (weight-at addr orig read-traces))))
      ;; Assume that replacements are added judiciously, namely to
      ;; random choices from the original trace (whose operators
      ;; didn't change due to other replacements?)
      (aif (assq addr replacements)
           (record-as-absorbed it)
           (if (compatible-operators-for? addr new orig)
               ;; One?  Should be one...
               (rdb-trace-search-one orig addr record-as-absorbed record-as-resampled)
               (record-as-resampled)))
      ;; TODO I believe the fresh and stale log likelihoods
      ;; mentioned in Wingate, Stuhlmuller, Goodman 2008 are
      ;; actually a distraction, in that they always cancel against
      ;; the log likelihood of newly sampled randomness.
      new-value)
    (set-rdb-record-hook! new regeneration-hook)
    (for-each
     (lambda (addr record)
       ;; Order (not counting issues with coupled primitives) will be
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
    new))

#;
`(begin
   (define x (flip))
   ,infer-defn
   (infer (lambda (t) (rebuild-rdb t '())))
   x)
