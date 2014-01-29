import math
import time

# Checks that the runtime of the unary function f(n)() is affine in its
# input (to wit, f(n)() takes An + B time to run, and A is decidedly
# nonzero).
def assertLinearTime(f):
  times = timings(f)
  (base_n,base_t) = times[0]
  norm_times = [(n - base_n, t - base_t) for (n,t) in times[1:]]
  # The notion is that the ratios of delta t to delta n should neither
  # systematically grow nor systematically shrink.
  ratios = [t/n for (n,t) in norm_times]
  differences = [ratios[i+1] - ratios[i] for i in range(len(ratios)-1)]
  ct_falling = len(filter(lambda r: r < 0, differences))
  # print times
  # print ratios
  assert ct_falling > len(ratios)*0.1, "Runtime of f is growing too fast.\nTimes: %r\nRatios: %r" % (times, ratios)
  assert ct_falling < len(ratios)*0.9, "Runtime of f is not growing fast enough.\nTimes: %r\nRatios: %r" % (times, ratios)

# Checks that the runtime of the unary function f(n)() does not depend
# on its input.
def assertConstantTime(f):
  times = timings(f)
  (base_n,base_t) = times[0]
  norm_times = [(n - base_n, t - base_t) for (n,t) in times[1:]]
  # The notion is that the ratios of delta t to delta n should neither
  # systematically grow nor systematically shrink.
  differences = [norm_times[i+1][1] - norm_times[i][1] for i in range(len(norm_times)-1)]
  ct_falling = len(filter(lambda r: r < 0, differences))
  # print times
  # print differences
  assert ct_falling > len(differences)*0.1, "Runtime of f is growing.\nTimes: %r\nDifferences: %r" % (times, differences)
  assert ct_falling < len(differences)*0.9, "Runtime of f is falling.\nTimes: %r\nDifferences: %r" % (times, differences)

# :: (Integer -> (() -> a)) -> [(Integer,Time)]
# Measures the runtime of the unary function f at several points.  The
# interface to the function (returning a thunk) permits it to have an
# untimed setup portion, for example building a large data structure
# and then testing that some operations on it do not depend on its
# size.
# The points are chosen so that
# - the thunk runs long enough to trust the accuracy of the clock
# - the whole process doesn't take too long
# - the produced values are useful for assessing the thunk's
#   asymptotic runtime.
def timings(f):
  def try_next(n):
    return int(math.floor(min(2*n,max(1.2*n, n+5))))
  def stop(duration, sample_ct):
    acceptable_duration = 1 # second
    if duration > acceptable_duration and sample_ct > 10:
      return True
    if duration > 3*acceptable_duration:
      return True
    if duration > 0.5 * acceptable_duration and sample_ct > 20:
      return True
    return False
  start_time = time.clock()
  (n,t) = min_measurable_input(f)
  answer = [(n,t)]
  now = time.clock()
  while not(stop(now - start_time, len(answer))):
    n = try_next(n)
    thunk = f(n)
    start = time.clock()
    thunk()
    end = time.clock()
    answer.append((n,end - start))
    now = end
  return answer

# :: (Integer -> (() -> a)) -> (Integer,Time)
# Returns a plausible input to the given function f such that f(input)()
# takes long enough to trust the accuracy of the clock, and the amount
# of time f(input)() took.  The assumption is that f will only get
# slower as its input is increased.
def min_measurable_input(f):
  clock_accuracy = 0.01 # seconds
  n = 1
  while True:
    thunk = f(n)
    start = time.clock()
    thunk()
    duration = time.clock() - start
    if duration > 10*clock_accuracy:
      return (n, duration)
    else:
      n *= 2
      if n > 2**50:
        raise Exception("f is too fast to measure")
