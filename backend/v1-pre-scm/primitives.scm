(declare (usual-integrations))

(define flip
  (make-primitive (lambda () (random 2))
                  (lambda (val) (log 0.5))))
