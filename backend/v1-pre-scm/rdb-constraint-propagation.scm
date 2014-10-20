(declare (usual-integrations apply eval))
(declare (integrate-external "syntax"))
(declare (integrate-external "pattern-case/pattern-case"))

;;; A candidate constraint propagation algorithm to statically migrate
;;; observations toward their assessability points, and so avoid
;;; trouble with constraining deterministic computations.

;;; I now think there may be a runtime solution to the same problem
;;; that's more general.

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
   (lambda (rec)
     (let ((exp (car rec))
           (env (cadr rec)))
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
          (case* (car rec)
            ((var x)
             (env-search (cadr rec) x
              (lambda (addr*)
                (rdb-backpropagate-constraint addr* value trace))
              (lambda ()
                ;; TODO Check for exact equality?
                (error "Can't constraint Scheme value" rec))))
            ((begin-form forms)
             (rdb-backpropagate-constraint
              (extend-address addr `(begin ,(- (length forms) 1)))
              value trace))
            ((application-form oper opands)
             (if (has-constant-shape? trace (extend-address addr `(app-sub 0)))
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
             (error "Cannot constrain non-random" (car rec)))))
        (lambda ()
          ;; TODO Check for exact equality?
          (error "Can't constrain external address" addr)))))
