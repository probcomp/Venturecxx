import math
import time
from nose.tools import assert_greater, assert_less

# Checks that the runtime of the unary function f(n)() is affine in its
# input (to wit, f(n)() takes An + B time to run, and A is decidedly
# nonzero).
def assertLinearTime(f, **kwargs):
  times = timings(f, **kwargs)
  (base_n,base_t) = times[0]
  norm_times = [(n - base_n, t - base_t) for (n,t) in times[1:]]
  # The notion is that the ratios of delta t to delta n should neither
  # systematically grow nor systematically shrink.
  ratios = [t/n for (n,t) in norm_times]
  differences = [ratios[i+1] - ratios[i] for i in range(len(ratios)-1)]
  ct_falling = len([r for r in differences if r < 0])
  # print times
  # print ratios
  # print differences
  assert_greater(ct_falling,len(differences)*0.2, "Runtime of f is growing too fast.\nTimes: %r\nRatios: %r" % (times, ratios))
  assert_less(ct_falling,len(differences)*0.8, "Runtime of f is not growing fast enough.\nTimes: %r\nRatios: %r" % (times, ratios))

# Checks that the runtime of the unary function f(n)() does not depend
# on its input.
def assertConstantTime(f, **kwargs):
  times = timings(f, **kwargs)
  (base_n,base_t) = times[0]
  norm_times = [(n - base_n, t - base_t) for (n,t) in times[1:]]
  # The notion is that the ratios of delta t to delta n should neither
  # systematically grow nor systematically shrink.
  differences = [norm_times[i+1][1] - norm_times[i][1] for i in range(len(norm_times)-1)]
  ct_falling = len([r for r in differences if r < 0])
  # print times
  # print differences
  assert ct_falling > len(differences)*0.2, "Runtime of f is growing.\nTimes: %r\nDifferences: %r" % (times, differences)
  assert ct_falling < len(differences)*0.8, "Runtime of f is falling.\nTimes: %r\nDifferences: %r" % (times, differences)

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
def timings(f, verbose=False, acceptable_duration=10, desired_sample_ct=20):
  def try_next(n):
    return int(math.floor(min(2*n,max(1.2*n, n+5))))
  def stop(duration, sample_ct):
    # acceptable_duration is in seconds
    if duration > acceptable_duration and sample_ct > 0.5 * desired_sample_ct:
      return True
    if duration > 0.5 * acceptable_duration and sample_ct > desired_sample_ct:
      return True
    return False
  start_time = time.clock()
  (n,t) = min_measurable_input(f)
  answer = [(n,t)]
  now = time.clock()
  while not stop(now - start_time, len(answer)):
    n = try_next(n)
    thunk = f(n)
    if verbose:
      print "Trying %s" % n
    start = time.clock()
    thunk()
    end = time.clock()
    answer.append((n,end - start))
    now = end
  if verbose:
    for (n, t) in answer:
      print "%s took %s s" % (n, t)
  return answer

# :: (Integer -> (() -> a)) -> (Integer,Time)
# Returns a plausible input to the given function f such that f(input)()
# takes long enough to trust the accuracy of the clock, and the amount
# of time f(input)() took.  The assumption is that f will only get
# slower as its input is increased.
def min_measurable_input(f):
  clock_accuracy = 0.01 # seconds
  acceptable_duration = 2 # seconds
  n = 1
  begin = time.clock()
  while True:
    thunk = f(n)
    start = time.clock()
    thunk()
    duration = time.clock() - start
    if duration > 10*clock_accuracy or n > 1000 or start - begin > acceptable_duration:
      return (n, duration)
    else:
      n *= 2


################# Temporary Hacks
def assertNLogNTime(f, slack=2, verbose=False):
  times = timings(f)
  if verbose:
    print times
  while times[0][0] <= 1:
    # This case would cause the below to throw a divide by zero
    times = times[1:]
  ns = [t[0] for t in times]
  ts = [t[1] for t in times]
  nlogns = [n * math.log(n) for n in ns]
  assert_less(max(ts) / min(ts), (max(nlogns) / min(nlogns)) * slack)
