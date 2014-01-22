import math
import time

# Checks that the runtime of the unary function f is affine in its
# input (to wit, f(n) takes An + B time to run, and A is decidedly
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
  assert ct_falling > len(ratios)*0.1, "Runtime of f is growing too fast.\nTimes: %r\nRatios: %r" % (times, ratios)
  assert ct_falling < len(ratios)*0.9, "Runtime of f is not growing fast enough.\nTimes: %r\nRatios: %r" % (times, ratios)

# :: (Integer -> a) -> [(Integer,Time)]
# Measures the runtime of the unary function f at several points,
# chosen so that
# - f runs long enough to trust the accuracy of the clock
# - the whole process doesn't take too long
# - the produced values are useful for assessing f's asymptotic
#   runtime.
def timings(f):
  def try_next(n):
    return int(math.floor(max(1.2*n, n+1)))
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
    f(n)
    end = time.clock()
    answer.append((n,end - now))
    now = end
  return answer

# :: (Integer -> a) -> (Integer,Time)
# Returns a plausible input to the given function f such that f(input)
# takes long enough to trust the accuracy of the clock, and the amount
# of time f(input) took.  The assumption is that f will only get
# slower as its input is increased.
def min_measurable_input(f):
  clock_accuracy = 0.01 # seconds
  n = 1
  while True:
    start = time.clock()
    f(n)
    duration = time.clock() - start
    if duration > 10*clock_accuracy:
      return (n, duration)
    else:
      n *= 2
      if n > 2**50:
        raise Exception("f is too fast to measure")
