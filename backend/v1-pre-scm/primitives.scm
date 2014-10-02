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

(define flip
  (make-sp
   (make-primitive
    (lambda (#!optional weight)
      (< (random 1.0)
         (if (default-object? weight)
             0.5
             weight))))
   (make-primitive
    (lambda (val #!optional weight)
      (log (if (default-object? weight)
               0.5
               (if val weight (- 1 weight))))))))

(define uniform
  (make-sp
   (make-primitive
    (lambda (low high)
      (+ low (random (exact->inexact (- high low))))))
   (make-primitive
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
     (define mu-flip
       (make-sp simulate-flip flip-log-density))))
