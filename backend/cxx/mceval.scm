;;; Expressions

;; <exp> := symbol
;;       := value
;;       := [references]

;; <list_exp> := [ref("lambda"), ref([symbol]), ref(exp)]
;;            := [ref("op_name"), ... refs of arguments]

;; Example Expressions
(define exp1 5)
(define exp2 (quote x))
(define exp3
  (map_list make_ref
	    (list (quote lambda) 
		  (list (quote x) (quote y))
		  (map_list make_ref (list (quote times) (quote x) (quote y))))))

(define exp4 (map_list make_ref (list exp3 5 8)))


;; References
(define make_ref (lambda (x) (lambda () x)))
(define deref (lambda (x) (x)))

;; Environments
;; { sym => ref }
(define initial_environment
  (list (make_map (list 'bernoulli 'normal)
		  (list bernoulli normal))))

(define extend_environment
  (lambda (syms vals outer_env) 
    (pair (make_map syms vals) outer_env)))

(define find_symbol 
  (lambda (sym env)
    (if (map_contains (first_frame env) sym)
	(map_lookup (first_frame env) sym)
	(find_symbol sym (rest env)))))

;; Application of compound
;; (env ids body)
(define incremental_apply
  (lambda (operator operands)
    (incremental_eval (list_ref operator 2)
		      (extend_environment (list_ref operator 0)
					  (list_ref operator 1)
					  operands))))

;; Returns a reference to the result of evaluating EXP in ENV
(define incremental_eval
  (lambda (exp env)
    (if (symbol? exp)
	(deref (find_symbol exp env))
	(if (not (pair? exp))
	    exp
	    (if (sym_eq (deref (list_ref exp 0)) (quote lambda))
		(pair env (rest exp)) ;; (env ids body)
		;; combination
		((lambda (operator operands)
		   (if (pair? operator)
		       (incremental_apply operator operands)
		       (apply operator operands)))
		 (incremental_eval (deref (list_ref exp 0)) env)
		 (map_list (lambda (x) (make_ref (incremental_eval (deref x) env))) (rest exp))))))))
