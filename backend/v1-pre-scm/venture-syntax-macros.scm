(define *the-model-trace*)

(define-syntax model-in
  (syntax-rules ()
    ((_ trace body-form ...)
     (fluid-let ((*the-model-trace* trace))
       body-form ...))))

(define-syntax assume
  (syntax-rules ()
    ((_ var form)
     (trace-in *the-model-trace*
      (define var form)))))

(define-syntax observe
  (syntax-rules ()
    ((_ form val-form)
     (trace-in *the-model-trace*
      ($observe form val-form))))) ; $observe is what observe-defn defines, but avoid name clash

(define-syntax infer
  (syntax-rules ()
    ((_ prog)
     (prog *the-model-trace*))))

(define-syntax predict
  (syntax-rules ()
    ((_ form)
     (trace-in *the-model-trace* form))))

;;; Here is what the examples from examples.scm look like with this syntax

;;; 1) Modeling in terms of inference

`(model-in (foo-extend (get-current-trace))
   (assume infer-param
    (mem (lambda (val prior_var)
           (model-in (bar-extend (get-current-trace))
             (assume theta (normal 0 prior_var)) ; traced in the inner trace
             (observe (normal theta 0.1) val) ; traced in the inner trace
             (infer (mh 'default 'one 10)) ; traced in the ambient model trace
             (predict theta)))))
   (assume variance_used (gamma 1 1))
   (observe (normal (infer-param 10 variance_used) 0.5) 10)
   (infer <something horrible>) ; traced completely outside
   (predict variance_used))

