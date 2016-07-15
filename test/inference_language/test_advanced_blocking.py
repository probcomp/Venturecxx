# Copyright (c) 2016 MIT Probabilistic Computing Project.
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

from venture.test.config import get_ripl

def testSmoke():
  # Basic tagging of random choices
  r = get_ripl()
  r.assume("a", "(tag 0 0 (normal 0 1))")
  r.assume("b", "(tag 0 1 (normal 0 1))")
  r.force("a", 1)
  r.force("b", 2)
  def both(ans):
    assert ans == [1, 2] or ans == [2, 1]
  def one(ans):
    assert ans == [1] or ans == [2]
  both(r.infer("""(do
  (s <- (select (minimal_subproblem (by_extent (by_top)))))
  (get_current_values s))"""))
  eq_([2], r.infer("""(do
  (s <- (select (minimal_subproblem (by_tag_value 0 1))))
  (get_current_values s))"""))
  both(r.infer("""(do
  (s <- (select (minimal_subproblem (by_tag 0))))
  (get_current_values s))"""))
  one(r.infer("""(do
  (s <- (select (minimal_subproblem (random_singleton (by_tag 0)))))
  (get_current_values s))"""))

  # Inference should move its target but not other stuff
  r.infer("(mh (minimal_subproblem (by_tag_value 0 1)) 1)")
  eq_(1, r.sample("a"))
  assert r.sample("b") != 2

def testSmoke2():
  # Same, but with the random choices slightly obscured
  r = get_ripl()
  r.assume("a", "(tag 0 0 ((lambda () (normal 0 1))))")
  r.assume("b", "(tag 0 1 ((lambda () (normal 0 1))))")
  r.force("a", 1)
  r.force("b", 2)
  def both(ans):
    assert ans == [1, 2] or ans == [2, 1]
  def one(ans):
    assert ans == [1] or ans == [2]
  both(r.infer("""(do
  (s <- (select (minimal_subproblem (by_extent (by_top)))))
  (get_current_values s))"""))
  eq_([2], r.infer("""(do
  (s <- (select (minimal_subproblem (by_tag_value 0 1))))
  (get_current_values s))"""))
  both(r.infer("""(do
  (s <- (select (minimal_subproblem (by_tag 0))))
  (get_current_values s))"""))
  one(r.infer("""(do
  (s <- (select (minimal_subproblem (random_singleton (by_tag 0)))))
  (get_current_values s))"""))

  # XXX This language interprets raw tags as touching arbitrary, not
  # necessarily random nodes.  As written, inference on a
  # deterministic node appears to be possible, but does nothing.
  r.infer("(mh (minimal_subproblem (by_tag_value 0 1)) 1)")
  eq_(1, r.sample("a"))
  assert r.sample("b") == 2

  # However, adding by_extent does what we would expect
  r.infer("(mh (minimal_subproblem (by_extent (by_tag_value 0 1))) 1)")
  eq_(1, r.sample("a"))
  assert r.sample("b") != 2

def testSmoke3():
  # Here's a variant that makes the difference between the local point
  # and the extent starker.
  r = get_ripl()
  r.assume("items", "(mem (lambda (i) (tag 'item i (normal 0 1))))")
  r.assume("total", "(tag 'total 0 (+ (items 1) (items 2) (items 3)))")
  r.force("(items 1)", 1)
  r.force("(items 2)", 2)
  r.force("(items 3)", 3)
  eq_(r.sample("total"), 6)
  def all(things):
    eq_([1, 2, 3], sorted(things))
  all(r.infer("""(do
  (s <- (select (minimal_subproblem (by_extent (by_tag 'total)))))
  (get_current_values s))"""))
