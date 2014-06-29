def derivative(f, x):
  return lambda(h): f(x+h) - f(x-h) / (2*h)

def richardson(f):
  # TODO Actually implement Richardson extrapolation
  return f(0.01)
