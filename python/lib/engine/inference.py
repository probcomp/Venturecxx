# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import time
from venture.lite.value import ExpressionType
from venture.ripl.utils import strip_types_from_dict_values
from pandas import DataFrame
from plot_spec import PlotSpec

class Infer(object):
  # In order to count iterations, can only have one call to each of printf, peek, plotf
  # This will still multi-count interations if you enter the identical printf command multiple times
  # I don't want these methods accessible to other modules, but Infer needs to access them
  # pylint:disable=protected-access
  def __init__(self, engine):
    self.engine = engine
    self.out = {}
    self.result = None

  def final_data(self):
    # add the last data point if result isn't None
    if self.result is not None: self.result._append_to_data()
    return self.result

  def _init_peek(self, names, exprs):
    if self.result is None:
      self.result = InferResult(first_command = 'peek')
    if self.result._spec_peek is None:
      self.result._init_peek(names, exprs)
    elif (names == self.result._spec_peek['names'] and
          exprs == self.result._spec_peek['exprs']):
      pass
    else:
      raise Exception("Cannot issue multiple peek commands in the same inference program")

  def _init_print(self, names, exprs):
    if self.result is None:
      self.result = InferResult(first_command = 'printf')
    if self.result._spec_print is None:
      self.result._init_print(names, exprs)
    elif (names == self.result._spec_print['names'] and
          exprs == self.result._spec_print['exprs']):
      pass
    else:
      raise Exception("Cannot issue multiple printf commands in same inference program")

  def _init_plot(self, spec, names, exprs):
    if self.result is None:
      self.result = InferResult(first_command = 'plotf')
    if self.result.spec_plot is None:
      self.result._init_plot(spec, names, exprs)
    elif (spec == self.result.spec_plot.spec_string and
          names == self.result.spec_plot.names and
          exprs == self.result.spec_plot.exprs):
      pass
    else:
      raise Exception("Cannot plot with different specs in the same inference program")

  def default_name_for_exp(self,exp):
    if isinstance(exp, basestring):
      return exp
    elif hasattr(exp, "__iter__"):
      return "(" + ' '.join([self.default_name_for_exp(e) for e in exp]) + ")"
    else:
      return str(exp)

  def default_names_from_exprs(self, exprs):
    return [self.default_name_for_exp(ExpressionType().asPython(e)) for e in exprs]

  def primitive_infer(self, exp): self.engine.primitive_infer(exp)
  def resample(self, ct): self.engine.resample(ct)
  def incorporate(self): pass # Since we incorporate at the beginning anyway
  def peek(self, *exprs):
    names = self.default_names_from_exprs(exprs)
    self._init_peek(names, exprs)
    self.result._add_data(self.engine, 'peek')
  def printf(self, *exprs):
    names = self.default_names_from_exprs(exprs)
    self._init_print(names, exprs)
    self.result._add_data(self.engine, 'printf')
    self.result.print_data()
  def plotf(self, spec, *exprs): # This one only works from the "plotf" SP.
    spec = ExpressionType().asPython(spec)
    names = self.default_names_from_exprs(exprs)
    self._init_plot(spec, names, exprs)
    self.result._add_data(self.engine, 'plotf')

class InferResult(object):
  '''
  Returned if any of "peek", "plotf", "printf" issued in an "infer" command.
  There may be at most one of each command per inference program.
  The "peek" command may give any number of model expressions. These will
  be recorded.
  Similarly, the "printf" command may give any number of model expressions, which
  will be recorded and printed as output on each iteration.
  See the SpecPlot class for more information on the arguments to plotf and
  the corresponding output.
  The dataset() method returns all data requested by any of the above commands
  as a Pandas DataFrame. By default, this data frame will always includes the
  sweep count, particle id, wall time, and global log score.
  Calling print will generate all plots stored in the spec_plot attribute. This
  attribute in turn is a SpecPlot object.
  '''
  def __init__(self, first_command):
    self.sweep = 0
    self.time = time.time()
    self._first_command = first_command
    self._spec_peek = None
    self._spec_print = None
    self.spec_plot = None

  def _init_peek(self, names, exprs):
    self._spec_peek = {'names' : names, 'exprs' : exprs}

  def _init_print(self, names, exprs):
    self._spec_print = {'names' : names, 'exprs' : exprs}

  def _init_plot(self, spec, names, exprs):
    self.spec_plot = SpecPlot(spec, names, exprs)

  def _add_data(self, engine, command):
    # if it's the first command, add all the default fields and increment the counter
    if command == self._first_command:
      self.sweep += 1
      self._append_to_data()
      self._collect_default_streams(engine)
    self._collect_data(engine, command)

  def _append_to_data(self):
    # self._this_data always defined on sweep 1
    # pylint: disable=access-member-before-definition
    if self.sweep == 1:
      pass
    elif self.sweep == 2:
      self.data = self._this_data
    else:
      for field in self.data:
        self.data[field].extend(self._this_data[field])
    # reset the data to record the current iteration
    self._this_data = {}

  def _collect_default_streams(self, engine):
    the_time = time.time() - self.time
    self._this_data['sweeps'] = [self.sweep] * len(engine.traces)
    self._this_data['particle'] = range(len(engine.traces))
    self._this_data['time (s)'] = [the_time] * len(engine.traces)
    self._this_data['log score'] = engine.logscore_all()

  def _collect_data(self, engine, command):
    elif command == 'peek':
      names = self._spec_peek['names']
      exprs = self._spec_peek['exprs']
    if command == 'printf':
      names = self._spec_print['names']
      exprs = self._spec_print['exprs']
    else:
      names = self.spec_plot.names
      exprs = self.spec_plot.exprs
    stack_dicts = [x.asStackDict() for x in exprs]
    for name, stack_dict in zip(names, stack_dicts):
      if name not in self._this_data:
        self._this_data[name] = engine.sample_all(stack_dict)

  def print_data(self):
    for name in self._spec_print['names']:
      if name == 'counter':
        print 'Sweep count: {0}'.format(self.sweep)
      elif name == 'time':
        print 'Wall time: {0:0.2f} s'.format(self._this_data['time (s)'])
      elif name == 'score':
        print 'Global log score: {0:0.2f}'.format(self._this_data['log score'])
      else:
        # TODO: support for pretty-printing of floats
        print '{0}: {1}'.format(name, strip_types_from_dict_values(self._this_data)[name])
    print

  def dataset(self):
    return DataFrame.from_dict(strip_types_from_dict_values(self.data))

  def draw(self):
    return self.spec_plot.draw(self.dataset())

  def plot(self):
    self.spec_plot.plot(self.dataset())

  def __str__(self):
    "Not really a string method, but does get itself displayed when printed."
    self.plot()
    return "a plot"

class SpecPlot(object):
  """(plotf spec exp0 ...) -- Generate a plot according to a format specification.

  Example:
    [INFER (cycle ((mh default one 1) (plotf c0s x)) 1000)]
  will do 1000 iterations of MH and then show a plot of the x variable
  (which should be a scalar) against the sweep number (from 1 to
  1000), colored according to the global log score.

  Example library use:
    ripl.infer("(cycle ((mh default one 1) (plotf c0s x)) 1000)")
  will return an object representing that same plot that will draw it
  if `print`ed.  The collected dataset can also be extracted from the
  object for more flexible custom plotting.

  The format specifications are inspired loosely by the classic
  printf.  To wit, each individual plot that appears on a page is
  specified by some line noise consisting of format characters
  matching the following regex

  [<geom>]*(<stream>?<scale>?){1,3}

  specifying
  - the geometric objects to draw the plot with
  - for each dimension (x, y, and color, respectively)
    - the data stream to use
    - the scale

  Each requested data stream is sampled once every time the inference
  program executes the plotf instruction, and the plot shows all of
  the samples after inference completes.

  The possible geometric objects are:
    _p_oint, _l_ine, _b_ar, and _h_istogram
  The possible data streams are:
    _<an integer>_ that expression, 0-indexed,
    _%_ the next expression after the last used one
    sweep _c_ounter, _t_ime (wall clock), log _s_core, and pa_r_ticle
  The possible scales are:
    _d_irect, _l_og

  TODO: Modifiers for how to treat multiple particles: distinguished
  (current implementation, good default), mean, median, all (what
  exactly would all mean?  2-D table? Splice and hope?)

  TODO: Modifiers for how to treat overplotting?  (Exactly identical
  discrete samples; continuous samples that are close enough for the
  points to overlap; control or good choice of point size?; 2D kernel
  density nonsense?)

  If one stream is indicated for a 2-D plot (points or lines), the x
  axis is filled in with the sweep counter.  If three streams are
  indicated, the third is mapped to color.

  If the given specification is a list, make all those plots at once.

  """
  def __init__(self, spec, names, exprs):
    self.spec_string = spec
    self.spec = PlotSpec(spec)
    self.names = names
    self.exprs = exprs

  def draw(self, data):
    if self.spec is None:
      pass
    else:
      return self.spec.draw(data, self.names)

  def plot(self, data):
    if self.spec is None:
      pass
    else:
      return self.spec.plot(data, self.names)
