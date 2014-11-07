import math
import time
import matplotlib.pyplot as plt

from venture.lite.utils import logaddexp

start_time = None
times = []
speed_ests = []

def log_weighted_avg(weights, vals):
  total = sum([math.exp(w)*v["value"] for (w,v) in zip(weights, vals)])
  weight = math.exp(logaddexp(weights))
  return total / weight

def collect(inferrer, step_speed):
  global start_time
  if start_time is None:
    start_time = time.time()
  times.append(time.time() - start_time)
  speed_ests.append(log_weighted_avg(inferrer.particle_weights(), step_speed))

def emit(_inferrer):
  print times
  print speed_ests
  plt.plot(times, speed_ests)
  plt.show()

def __venture_start__(ripl):
  ripl.bind_callback("collect", collect)
  ripl.bind_callback("emit", emit)
