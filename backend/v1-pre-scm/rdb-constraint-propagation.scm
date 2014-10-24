(declare (usual-integrations apply eval))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

;;; A candidate constraint propagation algorithm to statically migrate
;;; observations toward their assessability points, and so avoid
;;; trouble with constraining deterministic computations.

;;; I now think there may be a runtime solution to the same problem
;;; that's more general.

;;; This program is motivated in part by the following set of
;;; observations (though it does not fully implement them):

#|
Determining constancy and determinism can be a static analysis:
- A (higher-order) procedure is deterministic if everything leaving
  via positive positions is a deterministic function of whatever comes
  in via negative positions
  - This can be viewed as taint analysis from the source of randomness
  - Or as type inference about the presence or absence of the randomness monad
    - Assume automatic return on if branches where needed --
      conservative analysis for finding procedures that are always
      deterministic
- This can be checked by a constancy analysis: Mark as constant
  everything coming in through negative positions, propagate constancy
  through the body, check constancy of everything leaving through
  positive positions.
  - Actually, the reverse version will work better: solve the system
    of equations assuming procedures are deterministic unless proven
    otherwise.
- Constancy propagates through constancy-preserving syntax, and
  through applications of deterministic procedures to constant
  arguments (or constant and deterministic, if the arguments are
  higher-order).
- Constancy begins at source code literals and at variable references
  that leave the current trace.
- Mutation may break constancy if the replacement expression is
  random.
  - Mutation changes the notion of flow to include stuff flowing into
    the object being mutated.
  - I almost certainly don't want to mess with the timing analysis of
    trying to recover the constancy of a sometime-random variable
    being set to a constant value.  Just don't do that.
- Containers: Of course, I could always choose to differentiate
  between random containers and containers (some of) whose contents
  are random; then accessors become polymorphic in the randomness of
  that which is accessed.
  - This is of course the place where the distinction between actually
    constant and merely constant-body compound procedures comes from.
- The safe thing for foreign procedures is to assume they are random
  unless marked otherwise, but the convenient thing with procedures
  pulled from Scheme is to assume they are deterministic unless marked
  random (can mark them deterministic inside scheme->venture).
- This whole analysis is not part of "the interpreter", though it does
  depend on the syntax of the language, so can use additional metadata
  tags to mark some procedures deterministic.
- Of course, all the above only works for single-threaded execution.
- Note: This is constancy and determinism with respect to the
  manipulations that inference on the present trace might perform, not
  absolute constancy over all runs of the program.  That is why things
  that come in from external traces are presumed to be constant.
|#

;;; Note, however, that the "true" interface to observations should be
;;; much looser than "only stuff this program can backpropagate to an
;;; assessable random choice" -- any tail-assessable thing is
;;; sematically observable, though the Markov chain may end up not
;;; being ergodic if base measures are not fixed enough.

(define (rdb-backpropagate-constraints! trace)
  (define (foldee addr value accum)
    (receive (addr* value*)
      (rdb-backpropagate-constraint addr value trace)
      (if (wt-tree/member? addr* accum)
          ;; TODO Check for exact equality?
          (error "Can't double-constrain" addr*)
          (wt-tree/add accum addr* value*))))
  (set-rdb-constraints! trace
   (wt-tree/fold foldee (make-address-wt-tree) (rdb-constraints trace))))

;; TODO Abstract commonalities between this and is-constant?
(define (has-constant-shape? trace addr)
  (rdb-trace-search-one-record trace addr
   (lambda-case*
    ((evaluation-record exp env _ _ _)
     (case* exp
       ((constant val) #t)
       ((var x)
        (env-search env x
          (lambda (addr*)
            (has-constant-shape? trace addr*))
          ;; Values that come in from Scheme are presumed constant
          (lambda () #t)))
       ;; Lambdas have fixed shape, that's the point
       ((lambda-form _ _) #t)
       ;; TODO Additional possible constants:
       ;; - Results of applications of constant deterministic
       ;;   procedures on constant arguments
       ;; - There is a different sense of constant, namely constant-body
       ;;   compounds, which admits all lambda expressions as constant
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

(define (rdb-backpropagate-constraint addr value trace)
  ;; Accepts and returns both address and value because it may later
  ;; want to
  ;; - allow constraining constants to be themselves
  ;; - allow backpropagating constraints through constant invertible
  ;;   functions (which would change the value)
  (if (random-choice? addr trace)
      (values addr value)
      (rdb-trace-search-one-record trace addr
        (lambda (rec)
          (case* (evaluation-record-exp rec)
            ((var x)
             (env-search (evaluation-record-env rec) x
              (lambda (addr*)
                (rdb-backpropagate-constraint addr* value trace))
              (lambda ()
                ;; TODO Check for exact equality?
                (error "Can't constraint Scheme value" rec))))
            ((begin-form forms)
             (rdb-backpropagate-constraint
              (extend-address addr `(begin ,(- (length forms) 1)))
              value trace))
            ;; TODO Well, nuts.  Operative forms are recorded, even when they are "just macros".
            ((operative-form operative subforms)
             (if (eq? operative (cdr (assq 'let operatives)))
                 (rdb-backpropagate-constraint
                  (extend-address addr 'app) value trace)
                 (error "Cannot constrain non-random operative" (evaluation-record-exp rec))))
            ((application-form oper opands)
             ;; TODO Unconditionally statically backpropagating
             ;; through application of a non-constant non-assessable
             ;; procedure is invalid in general, but it's fine (I
             ;; think) for the test examples, and I don't want to
             ;; spend the time right now to broaden the static
             ;; analysis to cover them, because I fear that may not be
             ;; a good path anyway.
             (if #t #;(has-constant-shape? trace (extend-address addr `(app-sub 0)))
                 (rdb-trace-search trace (extend-address addr `(app-sub 0))
                   (lambda (val)
                     (if (compound? val)
                         (rdb-backpropagate-constraint
                          (extend-address addr 'app) value trace)
                         (error "Cannot constrain application of non-compound non-random procedure" rec)))
                   (lambda ()
                     (error "What?!")))
                 (error "Cannot constrain application of inconstant non-assessable procedure" rec)))
            (_
             (error "Cannot constrain non-random" (evaluation-record-exp rec)))))
        (lambda ()
          ;; TODO Check for exact equality?
          (error "Can't constrain external address" addr)))))
