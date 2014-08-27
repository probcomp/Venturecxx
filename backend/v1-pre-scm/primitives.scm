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

(define infer-defn
  '(define infer
     (lambda (prog)
       (begin
         (define t (get-current-trace))
         (ext (prog t))))))
