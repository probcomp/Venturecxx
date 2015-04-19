# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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
