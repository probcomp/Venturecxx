from venture.test.config import get_ripl
from venture import unit
from os import path, listdir
from itertools import product
import shutil

class HistoryChecker(unit.VentureUnit):
  def makeAssumes(self):
    self.assume('x', '(normal 0 10)')

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
