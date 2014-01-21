from venture.shortcuts import *
from stat_helpers import *
from test_globals import N, globalKernel

def RIPL(): return make_lite_church_prime_ripl()

# TODO the current version of this has been lost, so I need to make sure this old version works.

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
  return ripl

def computeF(x): return x * 5 + 5
def extractValue(d): 
  if type(d) is dict: return extractValue(d["value"])
  elif type(d) is list: return [extractValue(e) for e in d]
  else: return d

# TODO need to turn this into a test
# One option is to assert that we have gotten the right answer at some point in the first
# 5,000 iterations
def testIncrementalEvaluator1(N):
  ripl = RIPL()
  loadAll(ripl)
  
  ripl.assume("genBinaryOp","(lambda () (if (flip) (quote +) (quote *)))")
  ripl.assume("genLeaf","(lambda () (normal 3 2))")
  ripl.assume("genVar","(lambda (x) x)")

  ripl.assume("genExp","""
(lambda (x)
  (if (flip 0.7) 
      (genLeaf)
      (if (flip 0.9)
          (genVar x)
          (list (make_ref (genBinaryOp)) (make_ref (genExp x)) (make_ref (genExp x))))))
""")

  ripl.assume("noise","(gamma 2 2)")
  ripl.assume("exp","(genExp (quote x))")
  ripl.assume("concrete_exp","(concretizeExp exp)",label="exp")
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
    print extractValue(ripl.report("exp"))



def testIncrementalEvaluator2():
  "Incremental version of micro/test_basic_stats.py:testBernoulli1"
  ripl = RIPL()
  loadIncrementalEvaluator(ripl)
  ripl.predict("(incremental_eval (quote (branch (bernoulli 0.3) (normal 0.0 1.0) (normal 10.0 1.0))))")
  predictions = collectSamples(ripl,2,N)
  cdf = lambda x: 0.3 * stats.norm.cdf(x,loc=0,scale=1) + 0.7 * stats.norm.cdf(x,loc=10,scale=1)
  return reportTest(reportKnownContinuous("TestIncrementalEvaluator2", cdf, predictions, "0.7*N(0,1) + 0.3*N(10,1)"))

