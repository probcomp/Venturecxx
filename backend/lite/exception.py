class VentureError(Exception):
  """A runtime error with a stack trace."""
  stack_frame = None
  
  def __str__(self):
    return str(self.stack_frame) + '\n*** ' + self.message])

class VentureTypeError(VentureError):
  """This exception means that some SP was passed arguments of the wrong type."""

class VentureValueError(VentureError):
  """This exception means that some SP was passed an inappropriate value
of correct type (by analogy to ValueError in Python)."""

class VentureBuiltinSPMethodError(VentureError):
  """This exception means that an unimplemented method was called on a built-in PSP."""

class StackFrame(object):
  def __init__(self, exp, index, child=None):
    self.exp = exp
    self.index = index
    self.child = child
  
  def __str__(self):
    s = expToCode(self.exp)
    if self.child is not None:
      s += '\n' + str(self.child)
    return s

def expToCode(exp):
  if isinstance(exp, list):
    return '(%s)' % ' '.join(map(expToCode, exp))
  return str(exp)
