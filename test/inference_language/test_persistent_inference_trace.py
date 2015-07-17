# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

from nose.tools import eq_

from venture.test.config import get_ripl, on_inf_prim
from venture.lite import builtin

def testPersistenceSmoke1():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[define foo 5]
[assume x (flip 0.1)]
[infer (mh default one foo)]""")

def testPersistenceSmoke2():
  r = get_ripl(persistent_inference_trace=True)
  r.set_mode("venture_script")
  r.execute_program("""
define foo = 5
assume x = flip(0.1)
infer mh(default, one, foo)""")

def testPersistenceSmoke3():
  r = get_ripl(persistent_inference_trace=True)
  r.define("foo", "5")
  r.assume("x", "(flip 0.1)")
  r.infer("(mh default one foo)")

def testInferObserveSmoke1():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[assume x (normal 0 1)]
[infer (observe x (+ 1 2))]
[infer (incorporate)]""")
  eq_(3, r.sample("x"))

def testInferObserveSmoke2():
  r = get_ripl()
  r.infer("(observe (normal 0 1) 3 label)")
  r.infer("(incorporate)")
  eq_(3, r.report("label"))

def testInlineSMCSmoke():
  r = get_ripl(persistent_inference_trace=True)
  import venture.engine.inference_prelude as p
  r.execute_program("""
[define go
  (lambda (ct)
    (if (< ct 20)
        (begin
          (observe (normal 0 1) ct)
          (resample 1)
          (go (+ ct 1)))
        pass))]

[infer (go 0)]
[infer (incorporate)]
""")
  for i in range(20):
    eq_(i, r.report(i+len(p.prelude)+3))

def testInlineSMCSmoke2():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[assume frob (mem (lambda (i) (uniform_continuous -100 100)))]
[define go
  (lambda (ct)
    (if (< ct 20)
        (begin
          (observe (frob (unquote ct)) ct)
          (resample 1)
          (go (+ ct 1)))
        pass))]

[infer (go 0)]
[infer (incorporate)]
""")
  for i in range(20):
    eq_(i, r.sample("(frob %s)" % i))

def testDirectivesInInfer1():
  r = get_ripl()
  r.infer("(assume x 5)")
  eq_(5, r.sample("x"))

def testDirectivesInInfer2():
  r = get_ripl()
  r.infer("(predict (+ 5 2) foo)")
  eq_(7.0, r.report("foo"))

def testForeignInfSPs():
  r = get_ripl(persistent_inference_trace = True)
  r.bind_foreign_inference_sp("my_mul", builtin.builtInSPs()["mul"])
  r.infer("(mh default one (+ (my_mul 2 2) 1))")

def testForceSmoke1():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[assume x (normal 0 1)]
[define go (lambda () (force x 5))]
[infer (go)]""")
  x = r.sample('x')
  eq_(x, 5)

def testForceSmoke2():
  r = get_ripl(persistent_inference_trace=True)
  r.execute_program("""
[assume x (normal 0 1)]
[define go (lambda (y) (force x y))]""")
  r.infer("(go 2)")
  x = r.sample('x')
  eq_(x,2)
  r.infer("(go -3)")
  x = r.sample('x')
  eq_(x, -3)

@on_inf_prim("assume")
def testAssumeTracked():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.infer("(assume x (normal 0 1))")
  directives = ripl.list_directives()
  assert len(directives) == 1
  assert directives[0]["instruction"] == "assume"

@on_inf_prim("assume")
def testDirectivesTracked():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.infer("(assume x (normal 0 1))")
  ripl.infer("(observe (normal x 1) 2)")
  ripl.infer("(predict (normal x 1))")
  directives = ripl.list_directives()
  assert len(directives) == 3
  assert directives[0]["instruction"] == "assume"
  assert directives[1]["instruction"] == "observe"
  assert directives[2]["instruction"] == "predict"

@on_inf_prim("assume")
def testLabelingDirectives():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.infer("(assume x 5 foo)")
  ripl.infer("(observe (normal x 1) 2 bar)")
  ripl.infer("(predict (+ x 1) baz)")
  eq_(5, ripl.report("foo"))
  eq_(2, ripl.report("bar"))
  eq_(6, ripl.report("baz"))

@on_inf_prim("forget")
def testDirectivesForgettable():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.infer("(assume x 5 foo)")
  ripl.infer("(observe (normal x 1) 2 bar)")
  ripl.infer("(predict (+ x 1) baz)")
  assert len(ripl.list_directives()) == 3
  ripl.forget("bar")
  directives = ripl.list_directives()
  assert len(directives) == 2
  assert directives[0]["instruction"] == "assume"
  assert directives[1]["instruction"] == "predict"

@on_inf_prim("forget")
def testDirectivesForgettableFromInference():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.infer("(assume x 5 foo)")
  ripl.infer("(observe (normal x 1) 2 bar)")
  ripl.infer("(predict (+ x 1) baz)")
  assert len(ripl.list_directives()) == 3
  ripl.infer("(forget 'bar)")
  directives = ripl.list_directives()
  assert len(directives) == 2
  assert directives[0]["instruction"] == "assume"
  assert directives[1]["instruction"] == "predict"
  ripl.infer("(forget 'baz)")
  assert len(ripl.list_directives()) == 1
  ripl.infer("(forget 'foo)")
  assert len(ripl.list_directives()) == 0

@on_inf_prim("freeze")
def testDirectivesFreezableFromInference():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.infer("(assume x (normal 0 1) foo)")
  ripl.infer("(assume y (normal x 1) bar)")

  xval = ripl.sample("x")
  yval = ripl.sample("y")
  engine = ripl.sivm.core_sivm.engine
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],2)

  ripl.infer("(freeze 'bar)")
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],1)
  ripl.infer(30)
  assert not xval == ripl.sample("x")
  eq_(yval, ripl.sample("y"))
