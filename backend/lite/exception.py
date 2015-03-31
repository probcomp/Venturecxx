class VentureError(Exception):
  """A venture lite runtime error."""

class VentureTypeError(VentureError):
  """This exception means that some SP was passed arguments of the wrong type."""

class VentureValueError(VentureError):
  """This exception means that some SP was passed an inappropriate value
of correct type (by analogy to ValueError in Python)."""

class VentureBuiltinSPMethodError(VentureError):
  """This exception means that an unimplemented method was called on a built-in PSP."""

class SubsampledScaffoldError(VentureError):
  """This exception means that the subsampled scaffold cannot be constructed."""

class VentureCallbackError(VentureError):
  """This exception means that some (presumably user) callback failed."""
  def __init__(self, cause):
    super(VentureCallbackError, self).__init__()
    self.cause = cause
  def __str__(self):
    return "Callback failed:\n" + str(self.cause)

class VentureTimerError(VentureError):
  """This exception means that the inference callback timer was used incorrectly"""

class VentureWarning(UserWarning):
  '''Base class for Venture warnings'''
  pass

class GradientWarning(VentureWarning):
  '''Warnings related to gradients for automatic differentiation'''
  pass

class SubsampledScaffoldNotEffectiveWarning(VentureWarning):
  '''This warning means that the subsampled scaffold will be the same as a regular scaffold'''
  pass

class SubsampledScaffoldNotApplicableWarning(VentureWarning):
  '''This warning means that the subsampled scaffold cannot be constructed.'''
  pass

class SubsampledScaffoldStaleNodesWarning(VentureWarning):
  '''This warning means that the stale nodes may cause incorrect behavior.'''
  pass
