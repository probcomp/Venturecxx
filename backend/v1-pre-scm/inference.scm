(declare (usual-integrations apply eval))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

;;; Local resimulation-MH

(define (enforce-constraints trace)
  (receive (new-trace weight)
    (regen/copy trace (minimal-resimulation-maximal-reexecution-scaffold/one-target+deterministic-overrides trace #f (rdb-constraints trace)))
    (rdb-trace-commit! new-trace trace)))

(define *resimulation-mh-accept-hook* (lambda () 'ok))
(define *resimulation-mh-reject-hook* (lambda () 'ok))

(define ((mcmc-step* scaffolder) trace)
  ; (pp 'stepping)
  (let* ((target-addr (select-uniformly (random-choices trace)))
         (scaffold (scaffolder
                    trace target-addr (rdb-constraints trace))))
    ;; (rdb-trace-search-one-record trace target-addr pp (lambda () (error "What?")))
    (receive (torus detach-weight)
      (detach/copy trace scaffold)
      (receive (new-trace weight)
        (regen/copy trace scaffold)
        (let ((correction (- (log (length (random-choices trace)))
                             (log (length (random-choices new-trace))))))
          ; (pp `(step ,target-addr ,weight ,detach-weight ,correction))
          (if (< (log (random 1.0)) (+ weight detach-weight correction))
              (begin
                ; (display ".")
                (*resimulation-mh-accept-hook*)
                (rdb-trace-commit! new-trace trace))
              (begin
                ; (display "!")
                (*resimulation-mh-reject-hook*))))))))

(define mcmc-step (mcmc-step* minimal-resimulation-maximal-reexecution-scaffold/one-target+deterministic-overrides))

(define mcmc-defn
  '(define mcmc
     (lambda (steps)
       (lambda (t)
         (begin
           (enforce-constraints t)
           (map (lambda (i) (mcmc-step t))
                (iota steps)))))))

;;; Global rejection

;; The interface to providing bounds is to annotate the assessor
;; (coupled or otherwise) with a bounder procedure at value-bound-tag.
;; The bounder procedure gets the value, (the state if it's a coupled
;; assessor), and constancy marks for the arguments, and should return
;; an upper bound on the assessment.

;; A constancy mark is either #f to indicate the value may vary, or a
;; "just" record holding the constant value.

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
    (cond ((has-assessor? (car sub-vals))
           (do-bound (assessor-of (car sub-vals)) val constancies addr trace read-traces))
          ((has-coupled-assessor? (car sub-vals))
           (do-bound-coupled (coupled-assessor-of (car sub-vals))
                             val constancies addr trace read-traces))
          (else
           (error "What?!?")))))

(define (do-bound assessor val constancies addr trace read-traces)
  (if (not ((has-annotation? value-bound-tag) assessor))
      (error "Cannot absorb rejection at" val addr exp trace read-traces)
      (apply-in-void-subtrace
       ((annotation-of value-bound-tag) assessor)
       (cons val (cdr constancies)) ; cdr because I don't pass the operator itself
       '() addr trace read-traces)))

(define (do-bound-coupled op-coupled-assessor val constancies addr trace read-traces)
  (if (not ((has-annotation? value-bound-tag) op-coupled-assessor))
      (error "Cannot absorb rejection at" val addr exp trace read-traces)
      (case* (annotated-base op-coupled-assessor)
        ((coupled-assessor get _ _)
         ;; CONSIDER whether computing the bound for rejection
         ;; sampling a coupled assessable procedure even needs the
         ;; current state?  Should I just assume it varies across
         ;; samples and not pass it?  In that case, maybe the old
         ;; rejection bound algorithm (just mapping over the
         ;; constraints without rebuilding) is fine, if all the
         ;; bounder procedures ignore the auxiliary state anyway?
         (let ((cur-state (apply-in-void-subtrace get '() '() addr trace read-traces)))
           (apply-in-void-subtrace
            ((annotation-of value-bound-tag) op-coupled-assessor)
            (cons val (cons cur-state (cdr constancies))) ; cdr because I don't pass the operator itself
            '() addr trace read-traces))))))

(define (compute-bound exp env addr new read-traces answer)
  (if (or (resimulated? answer) (unchanged? answer))
      0
      (bound-for-at (absorbed-value answer) addr exp new read-traces)))

(define (rejection trace)
  (receive (new-trace weight+bound)
    (regen/copy trace
      (maximal-resimulation-scaffold/deterministic-overrides (rdb-constraints trace))
      #!default compute-bound + 0)
    ;; TODO Could use new-trace as a sample for a little bit of efficiency
    (let ((bound (cdr weight+bound)))
      (let loop ((tries 0))
        ; (pp `("Trying rejection" ,trace ,(rdb-constraints trace)))
        (receive (new-trace weight)
          (regen/copy trace (maximal-resimulation-scaffold/deterministic-overrides (rdb-constraints trace)))
          ; (pp `(got ,weight with bound ,bound))
          (if (< (log (random 1.0)) (- weight bound))
              (rdb-trace-commit! new-trace trace)
              (if (< tries 50)
                  (loop (+ tries 1))
                  (error "Rejected"))))))))
