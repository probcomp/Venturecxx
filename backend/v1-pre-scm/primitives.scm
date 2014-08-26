(declare (usual-integrations))

(define flip
  (make-primitive (lambda () (random 2))
                  (lambda (val) (log 0.5))))

(define infer-defn
  '(define infer
     (lambda (prog)
       (begin
         (define t (get-current-trace))
         (ext (prog t))))))
