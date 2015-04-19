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

# Framework for writing macros that resyntax errors.

# This code uses terminology that is slightly non-standard from the
# point of view of traditional macro systems.  Specifically:
#
# - a "macro" is an object that may transform an expression to a
#   "syntax" object.  Spiritually:
#
#     type Macro = Expression -> Maybe Syntax
#
# - a "syntax" is an object that can emit a macroexpanded expression,
#   and implements an isomorphism between indexes on the expanded and
#   unexpanded versions of the expression.  Spiritually:
#
#     type Syntax = (Expression, Index -> Index, Index -> Index)
#
# - an "index" is a path through an expression that indicates a
#   subexpression of interest (used for error reporting).
#   Spiritually:
#
#     type Index = Expression -> Expression
#
#   but they are represented explicitly, and transformed by syntaxs.
#
# Note that there is no notional separation between "macroexpand-1"
# and "macroexpand" (to use vocabulary from Common Lisp): the "syntax"
# object produced by one invocation of a "macro" is responsible for
# producing a fully macroexpanded expression.  This is accomplished by
# recursively invoking macroexpansion on subexpressions.
#
# Given that, macroexpansion proceeds simply by trying all known
# macros in order, using the result of the first that produces
# something -- see the top-level function `expand`.

from venture.exception import VentureException

class Macro(object):
  def __init__(self, predicate=None, expander=None, desc=None, intended_for_inference=False):
    self.predicate = predicate
    self.expander = expander
    self.desc = desc
    self._intended_for_inference = intended_for_inference

  def applies(self, exp):
    return self.predicate(exp)
  
  def expand(self, exp):
    return self.expander(exp)

  def intended_for_inference(self):
    return self._intended_for_inference

class Syntax(object):
  def desugared(self):
    """The desugared expression."""
    raise Exception("Not implemented!")
  
  def desugar_index(self, _index):
    """Desugar an expression index."""
    raise Exception("Not implemented!")
  
  def resugar_index(self, _index):
    """Transform the desugared expression index back into a sugared one."""
    raise Exception("Not implemented!")

def isSym(exp):
  return isinstance(exp, str)

def getSym(exp):
  if isSym(exp):
    return exp
  if isinstance(exp, dict):
    if exp['type'] == 'symbol':
      return exp['value']
  return None

macros = []

def register_macro(m):
  macros.append(m)

def expand(exp):
  for macro in macros:
    if macro.applies(exp):
      return macro.expand(exp)
  raise VentureException('parse', "Unrecognizable expression " + str(exp), expression_index=[])

def desugar_expression(exp):
  return expand(exp).desugared()

def sugar_expression_index(exp, index):
  return expand(exp).resugar_index(index)

def desugar_expression_index(exp, index):
  return expand(exp).desugar_index(index)
