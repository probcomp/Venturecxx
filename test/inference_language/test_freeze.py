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

from venture.test.config import broken_in, get_ripl, on_inf_prim

@on_inf_prim("freeze")
def testFreezeSanityCheck1():
  ripl = get_ripl()

  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("y", "(normal (normal (normal (normal (normal x 1.0) 1.0) 1.0) 1.0) 1.0)")

  engine = ripl.sivm.core_sivm.engine
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],6)

  ripl.freeze(2)
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],1)

@on_inf_prim("freeze")
def testFreezeSanityCheck2():
  ripl = get_ripl()

  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("y", "(tag 0 0 (normal (normal (normal (normal (normal x 1.0) 1.0) 1.0) 1.0) 1.0))")
  ripl.assume("ringer", "(tag 0 0 (normal 0.0 1.0))")

  engine = ripl.sivm.core_sivm.engine
  eq_(engine.getDistinguishedTrace().numNodesInBlock(0,0),6)

  ripl.freeze(2)
  eq_(engine.getDistinguishedTrace().numNodesInBlock(0,0),1)

@on_inf_prim("freeze")
def testFreezeSanityCheck3():
  """Check that a frozen value no longer changes under inference, even
though unfrozen ones do."""
  ripl = get_ripl()
  ripl.assume("x", "(normal 0.0 1.0)")
  ripl.assume("y", "(normal 0.0 1.0)")
  xval = ripl.sample("x")
  yval = ripl.sample("y")
  ripl.freeze(1)
  ripl.infer(100)
  eq_(xval, ripl.sample("x"))
  assert not yval == ripl.sample("y")

@broken_in("puma", "Puma still freezes shallowly")
def testFreezeMem():
  "Check that freezing affects all the values of a memmed procedure"
  ripl = get_ripl()
  ripl.assume("stdnorm", "(mem (lambda () (normal 0.0 1.0)))")
  ripl.assume("x", "(stdnorm)")
  engine = ripl.sivm.core_sivm.engine
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],1)
  ripl.freeze("x")
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],0)
  ripl.assume("y", "(stdnorm)")
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],0)
  eq_(ripl.sample("x"), ripl.sample("y"))

@broken_in("puma", "Puma still freezes shallowly")
def testPredictFreezeForget():
  "Check that predict-freeze-forget has an effect, if the freeze travels through the predicted expression."
  def freeze_exp(ripl, exp):
    ripl.predict(exp, label="do not clash with me")
    ripl.freeze("do not clash with me")
    ripl.forget("do not clash with me")

  ripl = get_ripl()
  ripl.assume("stdnorm", "(mem (lambda () (normal 0.0 1.0)))")
  ripl.assume("x", "(stdnorm)")
  engine = ripl.sivm.core_sivm.engine
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],1)
  freeze_exp(ripl, "x")
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],0)
  ripl.assume("y", "(stdnorm)")
  eq_(engine.get_entropy_info()["unconstrained_random_choices"],0)
  eq_(ripl.sample("x"), ripl.sample("y"))
