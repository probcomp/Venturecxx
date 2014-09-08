(declare (usual-integrations))

(define minus-inf
  (flo:with-exceptions-untrapped (flo:exception:divide-by-zero)
     (lambda ()
       (flo:/ -1. 0.))))

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
