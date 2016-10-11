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

from venture.test.config import broken_in
from venture.test.config import get_ripl
import venture.value.dicts as expr

@broken_in("puma", "Puma does not implement subproblem selection")
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

@broken_in("puma", "Puma does not implement subproblem selection")
def testGibbsSugarySmoke():
  # Gibbs should not crash with subproblem argument
  # This tests for Issue #634
  r = get_ripl()
  r.assume("b1", "(tag 'b integer<1> (flip 0.1))")
  r.assume("b2", "(tag 'b integer<2> (flip 0.1))")
  r.assume("c", "(flip (if (or b1 b2) 0.9 0.1))")
  r.set_mode("venture_script")
  r.observe("c", True)
  r.infer("gibbs(quote(b), integer<2>)")
  r.infer("gibbs(minimal_subproblem(/?b==integer<2>))")
  # the line below crashes:
  r.infer("gibbs(minimal_subproblem(by_tag_value(quote(b), integer<2>)))")

@broken_in("puma", "Puma does not implement subproblem selection")
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

@broken_in("puma", "Puma does not implement subproblem selection")
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
  def one(thing):
    assert thing == [1] or thing == [2] or thing == [3]
  all(r.infer("""(do
  (s <- (select (minimal_subproblem (by_extent (by_tag 'total)))))
  (get_current_values s))"""))
  one(r.infer("""(do
  (s <- (select (minimal_subproblem (random_singleton (by_extent (by_top))))))
  (get_current_values s))"""))
  one(r.infer("""(do
  (s <- (select (minimal_subproblem (by_extent (random_singleton (by_extent (by_top)))))))
  (get_current_values s))"""))

@broken_in("puma", "Puma does not implement subproblem selection")
def testSugarySmoke():
  # The sugared version of testSmoke3
  r = get_ripl()
  r.assume("items", "(mem (lambda (i) (tag 'item i (normal 0 1))))")
  r.assume("total", "(tag 'total 0 (+ (items 1) (items 2) (items 3)))")
  r.force("(items 1)", 1)
  r.force("(items 2)", 2)
  r.force("(items 3)", 3)
  eq_(r.sample("total"), 6)
  def all(things):
    eq_([1, 2, 3], sorted(things))
  def one(thing):
    assert thing == [1] or thing == [2] or thing == [3]
  r.set_mode("venture_script")
  all(r.infer("""{
  s <- select(minimal_subproblem(/?total));
  get_current_values(s)}"""))
  one(r.infer("""{
  s <- select(minimal_subproblem(random_singleton(/*)));
  get_current_values(s)}"""))

@broken_in("puma", "Puma does not implement subproblem selection")
def testPoster():
  r = get_ripl(seed=0)
  r.set_mode("venture_script")
  r.execute_program("""
assume alpha    ~ tag("hyper", "conc", gamma(1.0, 1.0));     // Concentration parameter
assume assign   = make_crp(alpha);                   // Choose the CRP representation
assume z        = mem((i) ~> { assign() });          // The partition on i induced by the DP
assume pct      = mem((d) ~> { tag("hyper", d, gamma(1.0, 1.0)) });           // Per-dimension hyper prior
assume theta    = mem((z, d) ~> { tag("compt", d, beta(pct(d), pct(d))) });   // Per-component latent
assume datum    = mem((i, d) ~> {                    // Per-datapoint:
  tag("row", i,
  tag("col", d, {
    cmpt ~ tag("clustering", pair(i, d), z(i));      // Select cluster
    weight ~ theta(cmpt, d);                         // Fetch latent weight
    flip(weight)}))});                               // Apply component model
""")
  dataset = [[0, 0, 0, 0, 0, 0],
             [1, 0, 0, 1, 0, 0],
             [1, 1, 0, 0, 0, 0],
             [0, 0, 0, 1, 0, 0],
             [1, 1, 0, 0, 0, 0],
             [0, 1, 1, 0, 1, 0]]
  def observe(i, d):
    r.observe(expr.app(expr.symbol("datum"), expr.integer(i), d), dataset[i][d])
  for i in range(6):
    for d in range(6):
      if r.sample("flip(0.7)"):
        observe(i, d)
  r.force("z(integer<3>)", expr.atom(8)) # A sentinel value that would not be assigned
  # Check that intersection picks out a row's cluster assignment.
  eq_([8], r.infer("""{
  s <- select(minimal_subproblem(by_intersection(
    by_extent(by_tag_value("row", integer<3>)),
    by_extent(by_tag("clustering")))));
  get_current_values(s)}"""))
  r.force("z(integer<4>)", expr.atom(8))
  # Check that union picks out several rows' cluster assignments.
  eq_([8, 8], r.infer("""{
  s <- select(minimal_subproblem(by_union(
    by_intersection(
      by_extent(by_tag_value("row", integer<3>)),
      by_extent(by_tag("clustering"))),
    by_intersection(
      by_extent(by_tag_value("row", integer<4>)),
      by_extent(by_tag("clustering"))))));
  get_current_values(s)}"""))

@broken_in("puma", "Puma does not implement subproblem selection")
def testSugaryPoster():
  # Same as above, but with syntactic sugar for the path expressions.
  r = get_ripl(seed=0)
  r.set_mode("venture_script")
  r.execute_program("""
assume alpha    ~ gamma(1.0, 1.0) #hyper:"conc";     // Concentration parameter
assume assign   = make_crp(alpha);                   // Choose the CRP representation
assume z        = mem((i) ~> { assign() });          // The partition on i induced by the DP
assume pct      = mem((d) ~> { gamma(1.0, 1.0) #hyper:d });           // Per-dimension hyper prior
assume theta    = mem((z, d) ~> { beta(pct(d), pct(d)) #compt:d });   // Per-component latent
assume datum    = mem((i, d) ~> {{                   // Per-datapoint:
  cmpt ~ z(i) #clustering;                           // Select cluster
  weight ~ theta(cmpt, d);                           // Fetch latent weight
  flip(weight)} #row:i #col:d});                     // Apply component model
""")
  dataset = [[0, 0, 0, 0, 0, 0],
             [1, 0, 0, 1, 0, 0],
             [1, 1, 0, 0, 0, 0],
             [0, 0, 0, 1, 0, 0],
             [1, 1, 0, 0, 0, 0],
             [0, 1, 1, 0, 1, 0]]
  def observe(i, d):
    r.observe(expr.app(expr.symbol("datum"), expr.integer(i), d), dataset[i][d])
  for i in range(6):
    for d in range(6):
      if r.sample("flip(0.7)"):
        observe(i, d)
  r.force("z(integer<3>)", expr.atom(8)) # A sentinel value that would not be assigned
  # Check that intersection picks out a row's cluster assignment.
  eq_([8], r.infer("""{
  s <- select(minimal_subproblem(/?row==integer<3>/?clustering));
  get_current_values(s)}"""))
  r.force("z(integer<4>)", expr.atom(8))
  # Check that union picks out several rows' cluster assignments.
  eq_([8, 8], r.infer("""{
  s <- select(minimal_subproblem(by_union(
    /?row==integer<3>/?clustering,
    /?row==integer<4>/?clustering)));
  get_current_values(s)}"""))
