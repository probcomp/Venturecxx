from venture.shortcuts import *
import math
import pdb

def RIPL(): return make_church_prime_ripl()

### Expressions

## <exp> := symbol
##       := value
##       := [references]

## <list_exp> := [ref("lambda"), ref([symbol]), ref(exp)]
##            := [ref("op_name"), ... refs of arguments]

## Example Expressions
ripl = RIPL()

## References
def loadReferences(ripl):
  ripl.assume("make_ref","(lambda (x) (lambda () x))")
  ripl.assume("deref","(lambda (x) (x))")

## Environments
## { sym => ref }
def loadEnvironments(ripl):
  ripl.assume("initial_environment","""
  (lambda () (list (make_map (list (quote bernoulli) (quote normal) (quote +) (quote *))
	                     (list (make_ref bernoulli) (make_ref normal) (make_ref plus) (make_ref times)))))
""")

  ripl.assume("extend_environment","""
  (lambda (outer_env syms vals) 
    (pair (make_map syms vals) outer_env))
""")

  ripl.assume("find_symbol","""
  (lambda (sym env)
    (if (map_contains (first env) sym)
	(map_lookup (first env) sym)
	(find_symbol sym (rest env))))
""")

## Application of compound
## operator = [&env &ids &body]
## operands = [&op1 ... &opN]
def loadEvaluator(ripl):
  ripl.assume("venture_apply","(lambda (op args) (eval (pair op (map_list deref args)) (get_empty_environment)))")

  ripl.assume("incremental_apply","""
  (lambda (operator operands)
    (incremental_eval (deref (list_ref operator 2))
		      (extend_environment (deref (list_ref operator 0))
					  (deref (list_ref operator 1))
					  operands)))
""")

  ripl.assume("incremental_eval","""
  (lambda (exp env)
    (if (is_symbol exp)
	(deref (find_symbol exp env))
	(if (not (is_pair exp))
	    exp
	    (if (= (deref (list_ref exp 0)) (quote lambda))
		(pair (make_ref env) (rest exp))
		((lambda (operator operands)
		   (if (is_pair operator)
		       (incremental_apply operator operands)
		       (venture_apply operator operands)))
		 (incremental_eval (deref (list_ref exp 0)) env)
		 (map_list (lambda (x) (make_ref (incremental_eval (deref x) env))) (rest exp)))))))
""")

def loadSampleExpressions(ripl):
  ripl.assume("exp1","5")
  ripl.assume("exp2","(quote bernoulli)")
  ripl.assume("exp3","(list (make_ref (quote +)) (make_ref 0.0) (make_ref 1.0))")
  ripl.assume("exp4","(list (make_ref (quote bernoulli)) (make_ref 0.5))")
  ripl.assume("exp5","(list (make_ref (quote normal)) (make_ref 0.0) (make_ref 1.0))")
  ripl.assume("exp6a","""
  (list (make_ref (quote lambda) )
        (make_ref (list (quote x)))
        (make_ref (list (make_ref (quote +)) (make_ref (quote x)) (make_ref (quote x)))))
""")

  ripl.assume("exp6","(list (make_ref exp6a) (make_ref 5) (make_ref 8))")

  ripl.assume("exp7a","""
  (list (make_ref (quote lambda) )
        (make_ref (list (quote x) (quote y)))
        (make_ref (list (make_ref (quote +)) (make_ref (quote x)) (make_ref (quote y)))))
""")

  ripl.assume("exp7","(list (make_ref exp7a) (make_ref 5) (make_ref 8))")

def loadAll():
  ripl = RIPL()
  loadReferences(ripl)
  loadEnvironments(ripl)
  loadEvaluator(ripl)
  loadSampleExpressions(ripl)
  return ripl

def evalExp(ripl):
  print ripl.predict("(incremental_eval exp1 (initial_environment))")
  print ripl.predict("(incremental_eval exp2 (initial_environment))")
  print ripl.predict("(incremental_eval exp3 (initial_environment))")
  print ripl.predict("(incremental_eval exp4 (initial_environment))")
  print ripl.predict("(incremental_eval exp5 (initial_environment))")
  print ripl.predict("(incremental_eval exp6 (initial_environment))")
  print ripl.predict("(incremental_eval exp7 (initial_environment))")
