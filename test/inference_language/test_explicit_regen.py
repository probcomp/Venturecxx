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

from venture.test.config import get_ripl, on_inf_prim, broken_in

@on_inf_prim("regen")
@broken_in("puma", "Does not support the regen SP yet")
def testDetachRegenSmoke():
  ripl = get_ripl(persistent_inference_trace=True)
  ripl.define("custom_mh", """\
(lambda (scope block)
  (do (subproblem <- (select scope block)) ; really, select by availability of log densities
      (rho_weight_and_rho_db <- (detach subproblem))
      (xi_weight <- (regen subproblem))
      (let ((rho_weight (first rho_weight_and_rho_db))
            (rho_db (rest rho_weight_and_rho_db)))
        (if (< (log (uniform_continuous 0 1)) (- xi_weight rho_weight))
            pass ; accept
            (do (detach subproblem) ; reject
                (restore subproblem rho_db))))))
""")
  ripl.assume("x", "(normal 0 1)")
  old = ripl.sample("x")
  ripl.infer("(custom_mh default all)")
  assert not old == ripl.sample("x")
