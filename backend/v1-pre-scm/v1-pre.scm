(declare (usual-integrations))

(define-structure (evaluation-context
                   (safe-accessors #t)
                   (conc-name evc-))
  exp
  env
  addr
  trace
  read-traces)

(define-structure address) ; Opaque

(define-structure (rdb (safe-accessors #t))
  )


