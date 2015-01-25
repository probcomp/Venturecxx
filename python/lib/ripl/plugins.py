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
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time

from venture.lite.exception import VentureTimerError
from venture.ripl.utils import strip_types

def __venture_start__(ripl):
  timer = Timer()
  ripl.bind_callback('timer_start', timer.start)
  ripl.bind_callback('timer_time', timer.print_time)
  ripl.bind_callback('timer_pause', timer.pause)
  ripl.bind_callback('timer_resume', timer.resume)
  ripl.bind_callback('dataset_to_file', dataset_to_file)

class Timer(object):
  'Timer object, whose methods will be used as inference callbacks.'
  def __init__(self):
    self.start_time = None
    self.downtime = None
    self.downtime_start = None
  def start(self, _=None):
    self.start_time = time()
    self.downtime = 0
  def time(self, _=None):
    if self.start_time is None or self.downtime is None:
      raise VentureTimerError('Timer has not been started.')
    now = time()
    if self.downtime_start is not None:
      extra_downtime = now - self.downtime_start
    else:
      extra_downtime = 0
    elapsed = now - self.start_time - self.downtime - extra_downtime
    return elapsed
  def print_time(self, _=None):
    elapsed = self.time()
    mins = elapsed // 60
    secs = elapsed % 60
    print 'Elapsed time: {0} m, {1:0.2f} s'.format(int(mins), secs)
  def pause(self, _=None):
    if self.downtime_start is not None:
      raise VentureTimerError('Timer is already paused.')
    self.downtime_start = time()
  def resume(self, _=None):
    if self.downtime_start is None:
      raise VentureTimerError('Timer is already running.')
    self.downtime += time() - self.downtime_start
    self.downtime_start = None

def dataset_to_file(inferrer, basename):
  '''
  Save all data recorded by inferrer to file "basename" in current directory.
  The basename must be quoted.
  Do not call this plugin as part of a (cycle) command with other inference
  statements that record data. Rather, use a (begin) and call this plugin
  after the cycle statement.
  '''
  # pylint:disable=protected-access
  # Hack so that the dataset gets the data from the last sweep
  inferrer.result._save_previous_iter(inferrer.result.sweep + 1)
  inferrer.result._final_appended = True
  ds = inferrer.result.dataset()
  basename = strip_types(basename)[0]
  ds.to_csv(basename + '.txt', sep = '\t',
            index = False, float_format = '%0.4f')
  print 'Dataset saved to ' + basename + '.txt'
