# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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
from venture.shortcuts import make_church_prime_ripl
import math
import pdb
from subprocess import call

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
  ripl.assume("incremental_initial_environment","""
(lambda () 
  (list 
    (make_map 
      (list (quote bernoulli) (quote normal) (quote +) (quote *))
      (list (make_ref bernoulli) (make_ref normal) (make_ref plus) (make_ref times)))))
""")

  ripl.assume("concrete_initial_environment","""
(lambda () 
  (list 
    (make_map 
      (list (quote bernoulli) (quote normal) (quote +) (quote *))
      (list bernoulli normal plus times))))
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
  ripl.assume("incremental_venture_apply","(lambda (op args) (eval (pair op (map_list deref args)) (get_empty_environment)))")

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
		       (incremental_venture_apply operator operands)))
		 (incremental_eval (deref (list_ref exp 0)) env)
		 (map_list (lambda (x) (make_ref (incremental_eval (deref x) env))) (rest exp)))))))
""")
  
def loadConcreteEvaluator(ripl):

  ripl.assume("concrete_venture_apply","(lambda (op args) (eval (pair op args) (get_empty_environment)))")

  ripl.assume("concrete_apply","""
  (lambda (operator operands)
    (concrete_eval (list_ref operator 2)
		      (extend_environment (list_ref operator 0)
					  (list_ref operator 1)
					  operands)))
""")

  ripl.assume("concrete_eval","""
  (lambda (exp env)
    (if (is_symbol exp)
	(find_symbol exp env)
	(if (not (is_pair exp))
	    exp
	    (if (= (list_ref exp 0) (quote lambda))
		(pair env (rest exp))
		((lambda (operator operands)
		   (if (is_pair operator)
		       (concrete_apply operator operands)
		       (concrete_venture_apply operator operands)))
		 (concrete_eval (list_ref exp 0) env)
		 (map_list (lambda (x) (concrete_eval x env)) (rest exp)))))))
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
  loadConcreteEvaluator(ripl)
#  loadSampleExpressions(ripl)
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
def extractValue(d): 
  if type(d) is dict: return extractValue(d["value"])
  elif type(d) is list: return [extractValue(e) for e in d]
  else: return d

def testIncrementalEvaluator(N):
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
                      (extend_environment (incremental_initial_environment) 
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
#    printExpression(ripl.trace,ripl.trace.getNode(expAddr).getValue())
#    val = ripl.trace.getNode(valAddr).getValue()
#    noise = ripl.trace.getNode(noiseAddr).getValue()
#    print "--> " + str(val) + " (" + str(noise) + ")"
#    vals.append(val)

#  mean = float(sum(vals))/len(vals)
#  print "---DemoChurchEval4---"
#  print "(5," + str(mean) + ")"


def runTests():
  ripl = RIPL()
  loadAll(ripl)

def renderDot(dot,i):
  name = "dot%d" % i
  dname = name + ".dot"
  oname = name + ".svg"
  f = open(dname,"w")
  f.write(dot)
  f.close()
  cmd = ["dot", "-Tsvg", dname, "-o", oname]
  call(cmd)
  print "written to file: " + oname

def computeIncrementalScaffolds(p,n,k):
  ripl = RIPL()
  loadAll(ripl)

  ripl.assume("genBinaryOp","(lambda () (if (flip) (quote +) (quote *)))")
  ripl.assume("genLeaf","(lambda () (normal 3 2))")
  ripl.assume("genVar","(lambda (x) x)")

  ripl.assume("p",str(p))
  ripl.assume("n",str(n))

  ripl.assume("genExp","""
(lambda (x n) 
(if (= n 0) (normal 3 2)
  (if (flip p)
      (list (make_ref (genBinaryOp)) (make_ref (genExp x (- n 1))) (make_ref (genExp x (- n 1))))
      (if (flip) (genLeaf) (genVar x)))))
  """)

  ripl.assume("exp","(genExp (quote x) n)",label="exp")

  ripl.assume("f","""
(mem 
  (lambda (y) 
    (incremental_eval exp
                      (extend_environment (incremental_initial_environment) 
                                          (list (quote x)) 
                                          (list (make_ref y))))))
""")
  ripl.assume("noise","(gamma 2 2)")
  ripl.assume("g","(lambda (z) (normal (f z) noise))")

  for x in range(k): ripl.predict("(g %d)" % x)

#  print extractValue(ripl.report("exp"))
  sizes = ripl.sivm.core_sivm.engine.getDistinguishedTrace().scaffold_sizes()
  return [sum(zones) for zones in sizes]

def computeConcreteScaffolds(p,n,k):
  ripl = RIPL()
  loadAll(ripl)

  ripl.assume("genBinaryOp","(lambda () (if (flip) (quote +) (quote *)))")
  ripl.assume("genLeaf","(lambda () (normal 3 2))")
  ripl.assume("genVar","(lambda (x) x)")

  ripl.assume("p",str(p))
  ripl.assume("n",str(n))

  ripl.assume("genExp","""
(lambda (x n) 
(if (= n 0) (normal 3 2)
  (if (flip p)
      (list (genBinaryOp) (genExp x (- n 1)) (genExp x (- n 1)))
      (if (flip) (genLeaf) (genVar x)))))
  """)

  ripl.assume("exp","(genExp (quote x) n)",label="exp")

  ripl.assume("f","""
(mem 
  (lambda (y) 
    (concrete_eval exp
                      (extend_environment (concrete_initial_environment) 
                                          (list (quote x)) 
                                          (list y)))))
""")
  ripl.assume("noise","(gamma 2 2)")
  ripl.assume("g","(lambda (z) (normal (f z) noise))")

  for x in range(k): ripl.predict("(g %d)" % x)

#  print extractValue(ripl.report("exp"))
  sizes = ripl.sivm.core_sivm.engine.getDistinguishedTrace().scaffold_sizes()
  return [sum(zones) for zones in sizes]

def computeBuiltinScaffolds(p,n,k):
  ripl = RIPL()

  ripl.assume("genBinaryOp","(lambda () (if (flip) (quote +) (quote *)))")
  ripl.assume("genLeaf","(lambda () (normal 3 2))")
  ripl.assume("genVar","(lambda (x) x)")

  ripl.assume("p",str(p))
  ripl.assume("n",str(n))

  ripl.assume("genExp","""
(lambda (x n) 
(if (= n 0) (normal 3 2)
  (if (flip p)
      (list (genBinaryOp) (genExp x (- n 1)) (genExp x (- n 1)))
      (if (flip) (genLeaf) (genVar x)))))
  """)

  ripl.assume("exp","(genExp (quote x) n)",label="exp")

  ripl.assume("f","""
(mem 
  (lambda (y) 
    (eval exp
          (extend_environment (get_current_environment) 
                              (quote x)
                              y))))
""")
  ripl.assume("noise","(gamma 2 2)")
  ripl.assume("g","(lambda (z) (normal (f z) noise))")

  for x in range(k): ripl.predict("(g %d)" % x)

#  print extractValue(ripl.report("exp"))
  sizes = ripl.sivm.core_sivm.engine.getDistinguishedTrace().scaffold_sizes()
  return [sum(zones) for zones in sizes]


def mean(seq): return float(sum(seq))/len(seq)
def var(seq): 
  mu = mean(seq)
  return sum([math.pow(float(x) - mu,2) for x in seq])/(len(seq)-1)

def collectAsymptotics(D):

  inc_sizes = [0 for x in range(D)]
  for d in range(D):
    seq = computeIncrementalScaffolds(1,d,1)
    inc_sizes[d] = mean(seq)

  print "incremental: " + str(inc_sizes)

  # con_sizes = [0 for x in range(D)]
  # for d in range(D):
  #   seq = computeConcreteScaffolds(1,d,1)
  #   con_sizes[d] = mean(seq)

  # print "concrete: " + str(con_sizes)

  con_sizes = [0 for x in range(D)]
  for d in range(D):
    seq = computeBuiltinScaffolds(1,d,1)
    con_sizes[d] = mean(seq)

  print "builtin: " + str(con_sizes)

  


#    printExpression(ripl.trace,ripl.trace.getNode(expAddr).getValue())
#    val = ripl.trace.getNode(valAddr).getValue()
#    noise = ripl.trace.getNode(noiseAddr).getValue()
#    print "--> " + str(val) + " (" + str(noise) + ")"
#    vals.append(val)

#  mean = float(sum(vals))/len(vals)
#  print "---DemoChurchEval4---"
#  print "(5," + str(mean) + ")"

  
