# Copyright (c) 2015 MIT Probabilistic Computing Project.
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
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time

from venture.lite.exception import VentureTimerError

def __venture_start__(ripl):
  ripl.bind_methods_as_callbacks(Timer(), prefix="timer_")

class Timer(object):
  'Timer object, whose methods will be used as inference callbacks.'
  def __init__(self):
    self._start_time = None
    self._downtime = None
    self._downtime_start = None
  def start(self, _=None):
    """Start a timer.

Resets any currently running timer that was started using ``timer_start``."""
    self._start_time = time()
    self._downtime = 0
  def _time(self, _=None):
    if self._start_time is None or self._downtime is None:
      raise VentureTimerError('Timer has not been started.')
    now = time()
    if self._downtime_start is not None:
      extra_downtime = now - self._downtime_start
    else:
      extra_downtime = 0
    elapsed = now - self._start_time - self._downtime - extra_downtime
    return elapsed
  def time(self, _=None):
    """Print the time that has elapsed since the timer was started by ``timer_start``."""
    elapsed = self._time()
    mins = elapsed // 60
    secs = elapsed % 60
    print 'Elapsed time: {0} m, {1:0.2f} s'.format(int(mins), secs)
  def pause(self, _=None):
    """Pause the timer started by ``timer_start``.

This is mainly for cumulative measurements (e.g. benchmarking) where
some sections should be excluded.

    """
    if self._downtime_start is not None:
      raise VentureTimerError('Timer is already paused.')
    self._downtime_start = time()
  def resume(self, _=None):
    """Resume a timer paused by ``timer_pause``."""
    if self._downtime_start is None:
      raise VentureTimerError('Timer is already running.')
    self._downtime += time() - self._downtime_start
    self._downtime_start = None
