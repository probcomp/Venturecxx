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

import scipy.stats as stats
from nose.tools import eq_
from nose.plugins.attrib import attr

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples, on_inf_prim

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
      (array (quote bernoulli) (quote normal) (quote add) (quote mul) (quote branch))
      (array (make_ref bernoulli) (make_ref normal) (make_ref add) (make_ref mul) (make_ref branch)))))
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

  ripl.assume("incremental_venture_apply","(lambda (op args) (eval (pair op (map_list deref args)) (get_empty_environment)))")

  ripl.assume("incremental_apply","""
  (lambda (operator operands)
    (incremental_eval (deref (lookup operator 2))
		      (extend_env (deref (lookup operator 0))
					  (deref (lookup operator 1))
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
  ripl.assume("map_list","""
(lambda (f xs)
  (if (is_pair xs)
      (pair (f (first xs))
            (map_list f (rest xs)))
      xs))
""")
  return ripl

def computeF(x): return x * 5 + 5

def extractValue(d): 
  if type(d) is dict: return extractValue(d["value"])
  elif type(d) is list: return [extractValue(e) for e in d]
  else: return d


@on_inf_prim("none")
def testIncrementalEvaluator1a():
  "Extremely basic test"
  ripl = get_ripl()
  loadAll(ripl)
  ripl.assume("expr","(quote 1)")
  ripl.assume("env","(incremental_initial_environment)")
  ripl.predict("(incremental_eval expr env)",label="pid")
  eq_(ripl.report("pid"),1)

@on_inf_prim("none")
def testIncrementalEvaluator1b():
  "Extremely basic test"
  ripl = get_ripl()
  loadAll(ripl)
  ripl.assume("expr","(list (make_ref add) (make_ref 1) (make_ref 1))")
  ripl.assume("env","(incremental_initial_environment)")
  ripl.predict("(incremental_eval expr env)",label="pid")
  eq_(ripl.report("pid"),2)

@statisticalTest
def testIncrementalEvaluator1c():
  "Incremental version of micro/test_basic_stats.py:testBernoulli1"
  ripl = get_ripl()
  loadAll(ripl)
  ripl.assume("expr","""
(list (make_ref branch)
      (make_ref (list (make_ref bernoulli)
                      (make_ref 0.3)))
      (make_ref (list (make_ref normal)
                      (make_ref 0.0)
                      (make_ref 1.0)))
      (make_ref (list (make_ref normal)
                      (make_ref 10.0)
                      (make_ref 1.0))))
""")
  ripl.assume("env","(incremental_initial_environment)")
  ripl.predict("(incremental_eval expr env)",label="pid")
  predictions = collectSamples(ripl,"pid")
  cdf = lambda x: 0.3 * stats.norm.cdf(x,loc=0,scale=1) + 0.7 * stats.norm.cdf(x,loc=10,scale=1)
  return reportKnownContinuous(cdf, predictions, "0.3*N(0,1) + 0.7*N(10,1)")

@attr('slow')
@on_inf_prim("mh")
def testIncrementalEvaluator2():
  "Difficult test. We make sure that it stumbles on the solution in a reasonable amount of time."
  ripl = get_ripl()

  loadAll(ripl)
  
  ripl.assume("genBinaryOp","(lambda () (if (flip) (quote add) (quote mul)))")
  ripl.assume("genLeaf","(lambda () (normal 4 3))")
  ripl.assume("genVar","(lambda (x) x)")

  ripl.assume("genExpr","""
(lambda (x)
  (if (flip 0.4) 
      (genLeaf)
      (if (flip 0.8)
          (genVar x)
          (list (make_ref (genBinaryOp)) (make_ref (genExpr x)) (make_ref (genExpr x))))))
""")

  ripl.assume("noise","(gamma 5 .2)")
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

  ripl.assume("square","(lambda (x) (mul x x))")
  X = 10
  predictStr = "(add "
  for x in range(X): predictStr += "(square (- (f %d) %d))" % (x,computeF(x))
  predictStr += ")"
  ripl.predict(predictStr,label="pid")
  for x in range(X): ripl.observe("(g %d)" % x,computeF(x))

  foundSolution = False
  # TODO These counts need to be managed so that this can consistently
  # find the right answer (this test may need tweaking once it runs)
  for _ in range(500):
    ripl.infer(10)
#    print ripl.report("pid")
    if ripl.report("pid") < 80: 
      foundSolution = True
      break

  assert foundSolution


