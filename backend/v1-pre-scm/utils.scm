(declare (usual-integrations))

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
