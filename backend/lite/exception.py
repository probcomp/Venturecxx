class VentureTypeError(Exception):
  """This exception means that some SP was passed arguments of the wrong type."""

class VentureValueError(Exception):
  """This exception means that some SP was passed an inappropriate value
of correct type (by analogy to ValueError in Python)."""

class VentureBuiltinSPMethodError(Exception):
  """This exception means that an unimplemented method was called on a built-in PSP."""
