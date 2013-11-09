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
(lambda () 
  (list 
    (make_map 
      (list (quote bernoulli) (quote normal) (quote +) (quote *))
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
					  (map_list deref (deref (list_ref operator 1)))
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
        (make_ref (list (make_ref (quote x))))
        (make_ref (list (make_ref (quote +)) (make_ref (quote x)) (make_ref (quote x)))))
""")

  ripl.assume("exp6","(list (make_ref exp6a) (make_ref 5) (make_ref 8))")

  ripl.assume("exp7a","""
  (list (make_ref (quote lambda) )
        (make_ref (list (make_ref (quote x)) (make_ref (quote y))))
        (make_ref (list (make_ref (quote +)) (make_ref (quote x)) (make_ref (quote y)))))
""")

  ripl.assume("exp7","(list (make_ref exp7a) (make_ref 5) (make_ref 8))")

def loadConcretize(ripl):
  ripl.assume("concretizeExp","""
(lambda (exp)
  (if (not (is_pair exp))
      exp
      (map_list (lambda (ref) (concretizeExp (deref ref))) exp)))
""")

def loadAll(ripl):
  loadReferences(ripl)
  loadEnvironments(ripl)
  loadEvaluator(ripl)
  loadConcretize(ripl)
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

def concretizeExp(ripl):
  print ripl.predict("(concretizeExp exp1)")
  print ripl.predict("(concretizeExp exp2)")
  print ripl.predict("(concretizeExp exp3)")
  print ripl.predict("(concretizeExp exp4)")
  print ripl.predict("(concretizeExp exp5)")
  print ripl.predict("(concretizeExp exp6)")
  print ripl.predict("(concretizeExp exp7)")


def computeF(x): return x * 5 + 5

def testIncrementalEvaluator(N):
  ripl = RIPL()
  loadAll(ripl)
  

  ripl.assume("genBinaryOp","(lambda () (if (flip) (quote +) (quote *)))")
  ripl.assume("genLeaf","(lambda () (normal 5 3))")
  ripl.assume("genVar","(lambda (x) x)")

  ripl.assume("genExp","""
(lambda (x)
  (if (flip) 
      (genLeaf)
      (if (flip)
          (genVar x)
          (list (make_ref (genBinaryOp)) (make_ref (genExp x)) (make_ref (genExp x))))))
""")

  ripl.assume("noise","(gamma 2 2)")
  ripl.assume("exp","(genExp (quote x))")
  ripl.assume("f","""
(mem 
  (lambda (y) 
    (incremental_eval exp 
                      (extend_environment (initial_environment) 
                                          (list (quote x)) 
                                          (list (make_ref y))))))
""")
  ripl.assume("g","(lambda (z) (normal (f z) noise))")

  ripl.assume("square","(lambda (x) (* x x))")
  X = 10
  predictStr = "(+ "
  for x in range(X): predictStr += "(square (- (f %d) %d))" % (x,computeF(x))
  predictStr += ")"
  ripl.predict(predictStr,label="pid")
  for x in range(X): ripl.observe("(g %d)" % x,computeF(x))

  vals = []
  for t in range(N):
    ripl.infer(50)
    print ripl.report("pid")
#    printExpression(ripl.trace,ripl.trace.getNode(expAddr).getValue())
#    val = ripl.trace.getNode(valAddr).getValue()
#    noise = ripl.trace.getNode(noiseAddr).getValue()
#    print "--> " + str(val) + " (" + str(noise) + ")"
#    vals.append(val)

#  mean = float(sum(vals))/len(vals)
#  print "---DemoChurchEval4---"
#  print "(5," + str(mean) + ")"
