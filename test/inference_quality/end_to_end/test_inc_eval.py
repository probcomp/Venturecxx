# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import scipy.stats as stats
from nose.tools import eq_
from nose.plugins.attrib import attr

from venture.test.stats import statisticalTest, reportKnownContinuous
from venture.test.config import get_ripl, collectSamples, on_inf_prim
from venture.test.config import broken_in

### Expressions

## <expr> := symbol
##        := value
##        := [references]

## <list_expr> := [ref("lambda"), ref([symbol]), ref(expr)]
##             := [ref("op_name"), ... refs of arguments]


## Environments
## { sym => ref }
def loadEnvironments(ripl):
  ripl.assume("incremental_initial_environment","""
(lambda ()
  (list
    (dict
      (array (quote bernoulli) (quote normal) (quote add)
             (quote mul) (quote biplex))
      (array (ref bernoulli) (ref normal) (ref add)
             (ref mul) (ref biplex)))))
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

  ripl.assume("incremental_venture_apply","""
(lambda (op args)
  (eval (pair op (map_list (lambda (x) (deref x)) args))
        (get_empty_environment)))""")

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
      (pair (ref env) (rest expr))
  ((lambda (operator operands)
     (if (is_pair operator)
         (incremental_apply operator operands)
         (incremental_venture_apply operator operands)))
   (incremental_eval (deref (lookup expr 0)) env)
   (map_list (lambda (x) (ref (incremental_eval (deref x) env)))
             (rest expr)))))))
""")


def loadAll(ripl):
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
@broken_in("puma", "Need to port records to Puma for references to work.  Issue #224")
def testIncrementalEvaluator1a():
  "Extremely basic test"
  ripl = get_ripl()
  loadAll(ripl)
  ripl.assume("expr","(quote 1)")
  ripl.assume("env","(incremental_initial_environment)")
  ripl.predict("(incremental_eval expr env)",label="pid")
  eq_(ripl.report("pid"),1)

@on_inf_prim("none")
@broken_in("puma", "Need to port records to Puma for references to work.  Issue #224")
def testIncrementalEvaluator1b():
  "Incremental appllication"
  ripl = get_ripl()
  loadAll(ripl)
  ripl.assume("expr","(list (ref add) (ref 1) (ref 1))")
  ripl.assume("env","(incremental_initial_environment)")
  ripl.predict("(incremental_eval expr env)",label="pid")
  eq_(ripl.report("pid"),2)

@on_inf_prim("none")
@broken_in("puma", "Need to port records to Puma for references to work.  Issue #224")
def testIncrementalEvaluator1c():
  "Incremental compound procedure"
  ripl = get_ripl()
  loadAll(ripl)
  ripl.assume("expr","(list (ref (list (ref 'lambda) (ref '()) (ref 1))))")
  ripl.assume("env","(incremental_initial_environment)")
  ripl.predict("(incremental_eval expr env)",label="pid")
  eq_(ripl.report("pid"),1.0)

@on_inf_prim("none")
@broken_in("puma", "Need to port records to Puma for references to work.  Issue #224")
def testIncrementalEvaluator1d():
  "Incremental compound with body"
  ripl = get_ripl()
  loadAll(ripl)
  ripl.assume("expr","""(list (ref (list (ref 'lambda) (ref '())
    (ref (list (ref add) (ref 1) (ref 1))))))""")
  ripl.assume("env","(incremental_initial_environment)")
  ripl.predict("(incremental_eval expr env)",label="pid")
  eq_(ripl.report("pid"),2.0)

@attr('slow')
@on_inf_prim("mh")
@broken_in("puma", "Need to port records to Puma for references to work.  Issue #224")
def testIncrementalEvaluator2():
  """Difficult test. We make sure that it stumbles on the solution
in a reasonable amount of time."""
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
          (list (ref (genBinaryOp))
                (ref (genExpr x)) (ref (genExpr x))))))
""")

  ripl.assume("noise","(gamma 5 .2)")
  ripl.assume("expr","(genExpr (quote x))")

  ripl.assume("f","""
(mem
  (lambda (y)
    (incremental_eval expr
                      (extend_env (incremental_initial_environment)
                                  (list (quote x))
                                  (list (ref y))))))
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
