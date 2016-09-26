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

from venture.exception import VentureException
from venture.test.config import collectSamples
from venture.test.config import get_ripl
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownDiscrete
from venture.test.stats import statisticalTest

@on_inf_prim("assume")
def testVentureScriptProgram():
  # At one point execute_program crashed with VentureScript.
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  ripl.execute_program("assume a = proc() {1}")

@on_inf_prim("none")
def testVentureScriptUnparseExpException():
  # At one point execute_program crashed with VentureScript.
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  try:
    ripl.execute_program("assume a = lambda")
  except VentureException as e:
    assert e.exception == "text_parse"
  else:
    assert False, "lambda is illegal in VentureScript and should raise a text_parse exception."

@statisticalTest
def testVentureScriptLongerProgram(seed):
  ripl = get_ripl(seed=seed)
  ripl.set_mode("venture_script")
  ripl.execute_program("assume is_tricky = flip(0.25); // end of line comments work\nassume coin_weight = if (is_tricky)\n{ uniform_continuous(0, 1) } \nelse {0.5};")
  ripl.predict("flip(coin_weight)", label="pid")
  ans = [(True, 0.5), (False, 0.5)]
  predictions = collectSamples(ripl, "pid", infer="10")
  return reportKnownDiscrete(ans, predictions)
