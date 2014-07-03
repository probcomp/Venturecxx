def derivative(f, x):
  return lambda(h): (f(x+h) - f(x-h)) / (2*h)

def richardson_step(f, degree):
  return lambda(h): (2**degree * f(h/2) - f(h)) / (2**degree - 1)

def richardson(f):
  # TODO Memoize the incoming function (possibly with an explicit
  # stream) to save compute on repeated evaluations at the same h

  # Could also implement the "stop when at machine precision" rule,
  # instead of always taking exactly four steps.
  return richardson_step(richardson_step(richardson_step(richardson_step(f, 2), 4), 6), 8)(0.001)

def tweaking_lens(lens, thunk):
  def f(h):
    x = lens.get()
    try:
      lens.set(x + h)
      ans = thunk()
      return ans
    finally:
      # Leave the value in the lens undisturbed
      lens.set(x)
  return f

def gradient_from_lenses(thunk, lenses):
  return [richardson(derivative(tweaking_lens(lens, thunk), 0)) for lens in lenses]
