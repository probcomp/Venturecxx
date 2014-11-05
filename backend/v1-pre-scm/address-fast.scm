(declare (usual-integrations))

(define-integrable (%make-address n)
  n)

(define-integrable (address? n)
  (fix:fixnum? n))

(define-integrable (address<? a1 a2)
  (fix:< a1 a2))

(define address-wt-tree-type number-wt-type)
