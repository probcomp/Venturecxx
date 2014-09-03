(declare (usual-integrations))

(define-syntax aif
  (sc-macro-transformer
   (lambda (exp env)
     (let ((ctest (close-syntax (cadr exp) env))
	   (cthen (make-syntactic-closure env '(it) (caddr exp)))
	   (celse (if (pair? (cdddr exp))
		      (list (close-syntax (cadddr exp) env))
		      '())))
       `(let ((it ,ctest))
	  (if it ,cthen ,@celse))))))

(define-syntax abegin1
  (sc-macro-transformer
   (lambda (exp env)
     (let ((object (close-syntax (cadr exp) env))
	   (forms (map (lambda (form)
                         (make-syntactic-closure env '(it) form))
                       (cddr exp))))
       `(let ((it ,object))
	  ,@forms
          it)))))

(define (search-parallel-lists item keys vals win lose #!optional =)
  (if (default-object? =)
      (set! = eq?))
  (let loop ((ks keys)
             (vs vals))
    (cond ((null? ks)
           (lose))
          ((= (car ks) item)
           (win (car vs)))
          (else (loop (cdr ks) (cdr vs))))))
