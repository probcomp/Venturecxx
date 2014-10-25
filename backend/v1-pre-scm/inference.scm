(declare (usual-integrations apply eval))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

(define (enforce-constraints trace)
  (receive (new-trace weight)
    (rebuild-rdb trace (propose-minimal-resimulation-with-deterministic-overrides #f (rdb-constraints trace)))
    (rdb-trace-commit! new-trace trace)))

(define *resimulation-mh-accept-hook* (lambda () 'ok))
(define *resimulation-mh-reject-hook* (lambda () 'ok))

(define (mcmc-step trace)
  (let ((target-addr (select-uniformly (random-choices trace))))
    ;; (rdb-trace-search-one-record trace target-addr pp (lambda () (error "What?")))
    (receive (new-trace weight)
      (rebuild-rdb trace (propose-minimal-resimulation-with-deterministic-overrides
                          target-addr (rdb-constraints trace)))
      (let ((correction (- (log (length (random-choices trace)))
                           (log (length (random-choices new-trace))))))
        (if (< (log (random 1.0)) (+ weight correction))
            (begin
              ; (display ".")
              (*resimulation-mh-accept-hook*)
              (rdb-trace-commit! new-trace trace))
            (begin
              ; (display "!")
              (*resimulation-mh-reject-hook*)))))))

(define mcmc-defn
  '(define mcmc
     (lambda (steps)
       (lambda (t)
         (begin
           (enforce-constraints t)
           (map (lambda (i) (mcmc-step t))
                (iota steps)))))))

;; Trick coin

(define trick-coin-example
  `(begin
     ,observe-defn
     (define model-trace (rdb-extend (get-current-trace)))
     (trace-in model-trace
               (begin
                 (define is-trick? (flip 0.5))
                 (define weight (if is-trick? (uniform 0 1) 0.5))
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 (define answer (list is-trick? weight))))
     (pp (trace-in (store-extend model-trace) answer))
     ,map-defn
     (enforce-constraints model-trace)
     (map (lambda (i) (mcmc-step model-trace))
          '(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20))
     (trace-in (store-extend model-trace) answer)))

;;; On observations: VKM argues that requiring observe to accept only
;;; a constant (!) (wrt current trace) procedure that has a density as
;;; the top expression is fine, for deep philosophical reasons.  The
;;; extra flexibility afforded by nesting and inference programming
;;; may go a long way to alleviating the trouble that causes.

;;; Hm.  The way I wrote this program, it never actually garbage
;;; collects old addresses from the trace, which has the two funny
;;; effects that
;;; a) Old choices stick around and may come back
;;; b) Proposals to shadow choices are made (and always accepted
;;;    because there is no likelihood)

(define trick-coin-example-syntax
  `(begin
     ,observe-defn
     ,map-defn
     ,mcmc-defn
     (model-in (rdb-extend (get-current-trace))
       (assume is-trick? (flip 0.5))
       (assume weight (if is-trick? (uniform 0 1) 0.5))
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (infer (mcmc 20))
       (predict (list is-trick? weight)))))

(define-structure (just (safe-accessors #t))
  >)

;; TODO Abstract commonalities between this and has-constant-shape?
(define (is-constant? trace addr)
  (rdb-trace-search-one-record trace addr
   (lambda-case*
    ((evaluation-record exp env _ _ _)
     (case* exp
       ((constant val) #t)
       ((var x)
        (env-search env x
          (lambda (addr*)
            (is-constant? trace addr*))
          ;; Values that come in from Scheme are presumed constant
          (lambda () #t)))
       ;; TODO Additional possible constants:
       ;; - Results of applications of constant deterministic
       ;;   procedures on constant arguments
       ;; - Lambda expressions that only close over constant things
       ;; - Constant tail positions of begin forms
       (_ #f))))
   (lambda ()
     (rdb-trace-search trace addr
      (lambda (v) #t) ; External values are constant
      (lambda ()
        ;; TODO Actually, it's still constant if it appears in any of
        ;; the read traces, even if it doesn't appear in parents of
        ;; this trace.
        (error "What?!"))))))

;; TODO Abstract commonalities between this and assessment+effect-at
;; This attempts to implement constant-detection for RandomDB traces.
;; The resulting interface to the bounding procedure is
;; that the argument will evaluate to #f if it is not known to be constant,
;; and to (make-just <value>) if it is.
(define (bound-for-at val addr exp trace read-traces)
  ;; Expect exp to be an application
  ;; Do not look for it in the trace itself because it may not have been recorded yet.
  (let* ((subaddrs (map (lambda (i)
                          (extend-address addr `(app-sub ,i)))
                        (iota (length exp))))
         (sub-vals (map (lambda (a)
                          (traces-lookup (cons trace read-traces) a))
                        subaddrs))
         (constancies (map (lambda (sub-addr sub-val)
                             (if (is-constant? trace sub-addr)
                                 (make-just sub-val)
                                 #f))
                           subaddrs sub-vals)))
    (if (not (annotated? (car sub-vals)))
        (error "What!?"))
    (if (not (has-assessor? (car sub-vals)))
        (error "What?!?"))
    (let ((assessor (assessor-of (car sub-vals))))
      (if (not ((has-annotation? value-bound-tag) assessor))
          (error "Cannot absorb rejection at" val addr exp trace read-traces)
          (apply-in-void-subtrace
           ((annotation-of value-bound-tag) assessor)
           (cons val (cdr constancies)) ; cdr because I don't pass the operator itself
           '() addr trace read-traces)))))

;; "Maximal" in the sense that it absorbs only when it must.  Returns
;; the density of the new trace, without subtracting off the density
;; of the old trace, together with the computed upper bound on
;; possible densities.  This is useful for rejection sampling.
(define ((propose-maximal-resimulation-with-deterministic-overrides+bound replacements)
         exp env addr new orig read-traces continue)
  (define (resampled)
    (values (continue) (cons 0 0)))            ; No weight, no bound
  (define (absorbed val)
    (receive (weight commit-state)
      (assessment+effect-at val addr exp new read-traces)
      (let ((bound (bound-for-at val addr exp new read-traces)))
        (commit-state)
        (values val (cons weight bound)))))
  ;; Assume that replacements are added judiciously, namely to
  ;; random choices from the original trace (whose operators
  ;; didn't change due to other replacements?)
  (search-wt-tree replacements addr
    (lambda (it)
      (if (random-choice? addr new)
          (absorbed it)
          (error "Trying to replace the value of a deterministic computation")))
    resampled))

;; "Maximal" in the sense that it absorbs only when it must.  Returns
;; the density of the new trace, without subtracting off the density
;; of the old trace.  This is suitable for rejection sampling once the
;; bound has been computed.
(define ((propose-maximal-resimulation-with-deterministic-overrides replacements)
         exp env addr new orig read-traces continue)
  (define (resampled)
    (values (continue) 0)) ; No weight
  (define (absorbed val)
    (receive (weight commit-state)
      (assessment+effect-at val addr exp new read-traces)
      (commit-state)
      (values val weight)))
  ;; Assume that replacements are added judiciously, namely to
  ;; random choices from the original trace (whose operators
  ;; didn't change due to other replacements?)
  (search-wt-tree replacements addr
    (lambda (it)
      (if (random-choice? addr new)
          (absorbed it)
          (error "Trying to replace the value of a deterministic computation")))
    resampled))

(define (rejection trace)
  (receive (new-trace weight+bound)
    (rebuild-rdb trace
     (propose-maximal-resimulation-with-deterministic-overrides+bound (rdb-constraints trace))
     (lambda (w+b total)
       (cons (+ (car w+b) (car total))
             (+ (cdr w+b) (cdr total))))
     (cons 0 0))
    ;; TODO Could use new-trace as a sample for a little bit of efficiency
    (let ((bound (cdr weight+bound)))
      (let loop ((tries 0))
        ; (pp `("Trying rejection" ,trace ,(rdb-constraints trace)))
        (receive (new-trace weight)
          (rebuild-rdb trace (propose-maximal-resimulation-with-deterministic-overrides (rdb-constraints trace)))
          ; (pp `(got ,weight with bound ,bound))
          (if (< (log (random 1.0)) (- weight bound))
              (rdb-trace-commit! new-trace trace)
              (if (< tries 50)
                  (loop (+ tries 1))
                  (error "Rejected"))))))))
