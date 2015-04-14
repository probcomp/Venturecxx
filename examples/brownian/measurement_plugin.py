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

import math
import time
import matplotlib.pyplot as plt

from venture.lite.utils import logaddexp

start_time = None
true_speed = 0
times = []
errors = []

def log_weighted_avg(weights, vals):
  total = sum([math.exp(w)*v["value"] for (w,v) in zip(weights, vals)])
  weight = math.exp(logaddexp(weights))
  return total / weight

def collect(inferrer, step_speed):
  global start_time
  if start_time is None:
    start_time = time.time()
  times.append(time.time() - start_time)
  speed_est = log_weighted_avg(inferrer.particle_log_weights(), step_speed)
  errors.append((speed_est - true_speed) * (speed_est - true_speed))

def emit(_inferrer):
  print times
  print errors
  plt.title("Estimation error")
  plt.xlabel("Time (s)")
  plt.ylabel("Error")
  plt.plot(times, errors)
  plt.savefig("brownian-error.png")
  print "Plot saved in brownian-error.png"

def __venture_start__(ripl):
  ripl.bind_callback("collect", collect)
  ripl.bind_callback("emit", emit)

def set_answer(answer):
  global true_speed
  true_speed = answer
