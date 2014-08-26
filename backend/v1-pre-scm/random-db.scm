(declare (usual-integrations))

;; TODO First writing a version that just forward simulates to make
;; sure the rest works.
(define-structure (rdb (safe-accessors #t))
  parent
  addresses
  records
  record-hook)

(define (rdb-trace-search trace addr win lose)
  (if (rdb? trace)
      (rdb-trace-search-one trace addr win
       (lambda () (trace-search (rdb-parent trace) addr win lose)))
      (lose)))

(define (rdb-trace-search-one trace addr win lose)
  (let loop ((as (rdb-addresses trace))
             (vs (rdb-records trace)))
    (cond ((null? as)
           (lose))
          ((eq? (car as) addr)
           (win (car (cddddr (car vs)))))
          (else (loop (cdr as) (cdr vs))))))

(define (rdb-trace-store! trace addr thing)
  (set-rdb-addresses! trace (cons addr (rdb-addresses trace)))
  (set-rdb-records! trace (cons thing (rdb-records trace))))

(define (rdb-record! trace exp env addr read-traces answer)
  (let ((real-answer
         (aif (rdb-record-hook trace)
              (it exp env addr read-traces answer)
              answer)))
    (rdb-trace-store! trace addr (list exp env addr read-traces real-answer))
    real-answer))

(define (rdb-extend trace)
  (make-rdb trace '() '() #f))

(define (rdb-empty)
  (make-rdb #f '() '() #f))

;;; Translation of the Lightweight MCMC algorithm to the present context

(define (rebuild-rdb orig replacements)
  (pp orig)
  (let ((new (rdb-extend (rdb-parent orig))))
    (define (regeneration-hook exp env addr read-traces answer)
      (pp exp)
      (aif (assq addr replacements)
           (cdr it)
           answer))
    (set-rdb-record-hook! new regeneration-hook)
    (for-each
     (lambda (addr record)
       ;; Order (not counting issues with coupled primitives) will be
       ;; enforced by evaluation recursion regardless of the order in
       ;; which the available expressions are traversed, provided the
       ;; replacement caches results.
       ;; However, I do need to order things so that defines get executed
       ;; before lookups of those symbols.
       ;; TODO: Mutation problem: define changes the evaluation environment!
       (case* record
         ((pair exp (pair env (pair addr (pair read-traces (pair answer null)))))
          (eval exp env new addr read-traces))))
     ;; Walking over exactly the expressions already recorded is the
     ;; right thing, because it will not attempt to rerun the extend
     ;; node that contains the executing inference program itself.
     (reverse (rdb-addresses orig))
     (reverse (rdb-records orig)))
    new))

#;
`(begin
   (define x (flip))
   ,infer-defn
   (infer (lambda (t) (rebuild-rdb t '()))))
