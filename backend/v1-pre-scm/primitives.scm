(declare (usual-integrations))

(define flip
  (make-primitive (lambda (#!optional weight)
                    (< (random 1.0)
                       (if (default-object? weight)
                           0.5
                           weight)))
                  (lambda (val #!optional weight)
                    (log (if (default-object? weight)
                             0.5
                             (if val weight (- 1 weight)))))))

(define uniform
  (make-primitive
   (lambda (low high)
     (+ low (random (exact->inexact (- high low)))))
   (lambda (val low high)
     (if (< low val high)
         (- (log (- high low)))
         -1e200 ; Poor man's negative infinity
         ))))

(define infer-defn
  '(define infer
     (lambda (prog)
       (begin
         (define t (get-current-trace))
         (ext (prog t))))))

(define observe-defn
  '(define observe
     (lambda (found desired)
       (begin
         (define t (get-current-trace))
         (define e (get-current-environment))
         (define addr (env-lookup e 'found))
         ;; When inference reruns the program, it will re-record the
         ;; constraint.  That might be fine.
         (record-constraint! t addr desired)))))
