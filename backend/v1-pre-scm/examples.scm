;;; Renditions of the examples in doc/v1/examples.md

;;; 1) Modeling in terms of inference:

;; This is necessarily a fragment that is itself being traced,
;; because it observes
`(begin
   (define infer-param
     (mem (lambda (val prior_var)
            `(begin
               (define model (foo-extend (get-current-trace)))
               (trace-in model
                (begin
                  (define theta (normal 0 prior_var))
                  ($observe (normal theta 0.1) val)))
               ((mh 'default 'one 10) model)
               (trace-in (store-extend model) theta)))))
   (define variance_used (gamma 1 1))
   ($observe (normal (infer-param 10 variance_used) 0.5) 10)
   variance_used)
;; The way this is written, there is no possibility to splice
;; infer-param, because it internally extends.

;;; 2) Conditional observation and inference:

`(begin
   (define model-trace (foo-extend (get-current-trace)))
   (trace-in model-trace ; If this were in a let, add_data_and_predict wouldn't work anymore
    (begin
      (define is_trick (bernoulli 0.1))
      (define weight (if is_trick (uniform_continuous 0 1) 0.5))))
   (define add_data_and_predict
     (lambda (trace)
       (trace-in trace
        ($observe (bernoulli weight) #t))  ; Same weight because trace-in splices environments!
       ((mh 'default 'one 10) trace)))
   (define find-trick
     (lambda (trace)
       (if (not (trace-in trace is_trick))
           (begin
             (add_data_and_predict trace)
             (find-trick trace)))))
   (find-trick model-trace)
   (trace-in model-trace weight))

;;; 2') Conditional observation and inference 2 Actually reads the same now.

;;; 3) Inference by modeling

`(begin
   (define model-trace (foo-extend (get-current-trace)))
   (trace-in model-trace
    (begin
      (define some stuff)
      ($observe (some stuff) #t)))
   (define my-inference-scheme
     (lambda (trace)
       (define meta-model-trace (bar-extend trace)) ;; This way the meta-model can read the model
       (trace-in meta-model-trace
        (begin
          (define meta-some stuff)
          ($observe (meta-some meta-stuff) #t)))
       ((mh 'default 'one 10) meta-model-trace)))
   (my-inference-scheme model-trace))

;;; My read on 4) is that it depends on how INFER is defined in terms
;;; of trace-in and friends.  Does it escape its enclosing trace?  If
;;; so, to what?
