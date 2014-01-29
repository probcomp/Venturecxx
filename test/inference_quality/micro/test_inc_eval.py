# Copyright (c) 2013, MIT Probabilistic Computing Project.
# 
# This file is part of Venture.
# 	
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 	
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 	
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from venture.test.stats import *
from nose import SkipTest
import math

### Expressions

## <expr> := symbol
##       := value
##       := [references]

## <list_expr> := [ref("lambda"), ref([symbol]), ref(expr)]
##            := [ref("op_name"), ... refs of arguments]


## References
def loadReferences(ripl):
  ripl.assume("make_ref","(lambda (x) (lambda () x))")
  ripl.assume("deref","(lambda (x) (x))")

## Environments
## { sym => ref }
def loadEnvironments(ripl):
  ripl.assume("incremental_initial_environment","""
(lambda () 
  (list 
    (dict 
      (list (quote bernoulli) (quote normal) (quote +) (quote *))
      (list (make_ref bernoulli) (make_ref normal) (make_ref plus) (make_ref times)))))
""")

  ripl.assume("extend_env","""
  (lambda (outer_env syms vals) 
    (pair (dict syms vals) outer_env))
""")

  ripl.assume("find_symbol","""
  (lambda (sym env)
    (if (contains (first env) sym)
	(lookup (first env) sym)
	(find_symbol sym (rest env))))
""")

## Application of compound
## operator = [&env &ids &body]
## operands = [&op1 ... &opN]
def loadIncrementalEvaluator(ripl):
  # TODO Replace list_ref with a builtin?
  ripl.assume("list_ref","""
(lambda (lst i)
  (if (eq 0 i)
      (first lst)
      (list_ref (second lst) (minus i 1))))""")
  ripl.assume("incremental_venture_apply","(lambda (op args) (eval (pair op (map_list deref args)) (get_empty_environment)))")

  ripl.assume("incremental_apply","""
  (lambda (operator operands)
    (incremental_eval (deref (lookup operator 2))
		      (extend_env (deref (lookup operator 0))
					  (map_list deref (deref (lookup operator 1)))
					  operands)))
""")

  ripl.assume("incremental_eval","""
  (lambda (expr env)
    (if (is_symbol expr)
	(deref (find_symbol expr env))
	(if (not (is_pair expr))
	    expr
	    (if (= (deref (lookup expr 0)) (quote lambda))
		(pair (make_ref env) (rest expr))
		((lambda (operator operands)
		   (if (is_pair operator)
		       (incremental_apply operator operands)
		       (incremental_venture_apply operator operands)))
		 (incremental_eval (deref (lookup expr 0)) env)
		 (map_list (lambda (x) (make_ref (incremental_eval (deref x) env))) (rest expr)))))))
""")
  

def loadAll(ripl):
  loadReferences(ripl)
  loadEnvironments(ripl)
  loadIncrementalEvaluator(ripl)
  return ripl

def computeF(x): return x * 5 + 5

def extractValue(d): 
  if type(d) is dict: return extractValue(d["value"])
  elif type(d) is list: return [extractValue(e) for e in d]
  else: return d


@statisticalTest
def testIncrementalEvaluator1():
  "Incremental version of micro/test_basic_stats.py:testBernoulli1"
  raise SkipTest("Errors out due to a Venture-level type error (a string flowed into operator position).  Re-enable when there are facilities for debugging such things.  Issue https://app.asana.com/0/9277419963067/9280122191537")
  ripl = get_ripl()
  loadAll(ripl)
  ripl.predict("(incremental_eval (quote (branch (bernoulli 0.3) (normal 0.0 1.0) (normal 10.0 1.0))))")
  predictions = collectSamples(ripl,2)
  cdf = lambda x: 0.3 * stats.norm.cdf(x,loc=0,scale=1) + 0.7 * stats.norm.cdf(x,loc=10,scale=1)
  return reportKnownContinuous("TestIncrementalEvaluator1", cdf, predictions, "0.3*N(0,1) + 0.7*N(10,1)")


def testIncrementalEvaluator2():
  "Difficult test. We make sure that it stumbles on the solution in a reasonable amount of time."
  raise SkipTest("Errors out due to a Venture-level type error (something wanted a list as an argument and got a float).  Re-enable when there are facilities for debugging such things.  Issue https://app.asana.com/0/9277419963067/9280122191537")
  ripl = get_ripl()

  loadAll(ripl)
  
  ripl.assume("genBinaryOp","(lambda () (if (flip) (quote +) (quote *)))")
  ripl.assume("genLeaf","(lambda () (normal 3 2))")
  ripl.assume("genVar","(lambda (x) x)")

  ripl.assume("genExpr","""
(lambda (x)
  (if (flip 0.7) 
      (genLeaf)
      (if (flip 0.9)
          (genVar x)
          (list (make_ref (genBinaryOp)) (make_ref (genExpr x)) (make_ref (genExpr x))))))
""")

  ripl.assume("noise","(gamma 2 2)")
  ripl.assume("expr","(genExpr (quote x))")

  ripl.assume("f","""
(mem 
  (lambda (y) 
    (incremental_eval expr 
                      (extend_env (incremental_initial_environment) 
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

  foundSolution = False
  # TODO These counts need to be managed so that this can consistently
  # find the right answer (this test may need tweaking once it runs)
  for _ in range(25):
    ripl.infer(10)
    if ripl.report("pid") < 1: 
      foundSolution = True
      break

  assert foundSolution


