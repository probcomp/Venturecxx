(declare (usual-integrations))

;;; The notion of procedures

; data BasicProcedure = Compound | Primitive
; data Procedure = Basic BasicProcedure
;                | Full (Maybe BasicProcedure) -- simulator
;                       (Maybe BasicProcedure) -- assessor
;
; There is a funny use case of assessors that are Full rather than
; Basic Procedures.  To wit, if exact assessment is infeasible, it may
; be approximate, in which case it may be stochastic, in which case it
; may be interesting to itself assess.  However, a Compound Basic
; Procedure can consist of a call to a (closed-over) Full Procedure,
; so we handle that use case.

; However, it is easy to code the slightly type-looser version, namely
; Full Procedures containing optional Procedures.  That way, apply
; recurs into itself.

(define assessor-tag (make-annotation-tag))

(define (make-sp simulator assessor)
  (annotate simulator assessor-tag assessor))

;; Tag for annotating procedures with ordered outputs with metadata
;; indicating upper bounds.  This is used to compute the bound for
;; rejection sampling.
;; TODO Add support for rejection sampling where assessment and
;; bounding are not possible separately but where the ratio can
;; nonetheless be computed (does that ever happen?).  Implementation
;; strategy: another tag, intended for annotating the simulator, and
;; another clause in bound-for-at.
(define value-bound-tag (make-annotation-tag))

(define flip
  (make-sp
   (scheme-procedure-over-values->v1-foreign
    (lambda (#!optional weight)
      (< (random 1.0)
         (if (default-object? weight)
             0.5
             weight))))
   (annotate
    (scheme-procedure-over-values->v1-foreign
     (lambda (val #!optional weight)
       (log (if (default-object? weight)
                0.5
                (if val weight (- 1 weight))))))
    value-bound-tag
    (scheme-procedure-over-values->v1-foreign
     (lambda (val #!optional weight)
       (if (default-object? weight)
           (log 0.5)
           0))))))

(define uniform
  (make-sp
   (scheme-procedure-over-values->v1-foreign
    (lambda (low high)
      (+ low (random (exact->inexact (- high low))))))
   (scheme-procedure-over-values->v1-foreign
    (lambda (val low high)
      (if (< low val high)
          (- (log (- high low)))
          minus-inf)))))

(define observe-defn
  '(define $observe
     (lambda (found desired)
       (begin
         (define t (get-current-trace))
         (define e (get-current-environment))
         (define addr (env-lookup e 'found))
         ;; When inference reruns the program, it will re-record the
         ;; constraint.  That might be fine.
         (record-constraint! t addr desired)))))

(define map-defn
  '(define map
     (lambda (f lst)
       (if (pair? lst)
           (cons (f (car lst)) (map f (cdr lst)))
           lst))))

(define mu-flip-defn
  `(begin
     (define simulate-flip
       (lambda (weight)
         (< (random 1.0) weight)))
     (define flip-log-density
       (lambda (b weight)
         (log (if b weight (- 1 weight)))))
     (define flip-log-density-bound
       (lambda (b weight) 0))
     (define mu-flip
       (make-sp simulate-flip (annotate flip-log-density value-bound-tag flip-log-density-bound)))))
