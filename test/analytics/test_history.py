# Copyright (c) 2014 MIT Probabilistic Computing Project.
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

from os import path, listdir
from itertools import product
import shutil
from nose.plugins.attrib import attr

from venture.test.config import get_ripl, gen_on_inf_prim
from venture import unit

class HistoryChecker(unit.VentureUnit):
  def makeAssumes(self):
    self.assume('x', '(normal 0 10)')

@attr("slow")
@gen_on_inf_prim("none")
def test_plot():
  for output_format in ['pdf', 'png']:
    yield check_plot, output_format

def check_plot(output_format):
  '''minimal test ensuring that attempting to plot output doesn't break'''
  ripl = get_ripl()
  model = HistoryChecker(ripl)
  history = model.runFromJoint(5)
  out = path.join(path.dirname(path.realpath(__file__)), 'testme')
  try:
    history.plot(fmt = output_format, directory = out + '/')
  except Exception as my_exception:
    raise my_exception
  else:
    # spot check that a couple plots got dumped
    check_plot_existence(output_format, out)
  finally:
    # clean up
    if path.exists(out): shutil.rmtree(out)

def check_plot_existence(output_format, out):
  '''Make sure that the plots are where they should be'''
  all_plots = listdir(out)
  variables = ['x', 'sweep_time_(s)', 'sweep_iters', 'logscore']
  plot_types = ['hist', 'series']
  for variable, plot_type in product(variables, plot_types):
    assert variable + '_' + plot_type + '.' + output_format in all_plots
