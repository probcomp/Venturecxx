#!/usr/bin/env python

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

import sys
import re

from venture.lite.builtin import builtInSPsList
from venture.lite.inference_sps import inferenceSPsList
from venture.engine import inference_prelude
from venture.sivm.macro_system import macros
from venture.shortcuts import Lite

def print_sorted_first_component(xs):
  names = sorted([x[0] for x in xs if not re.match("^_", x[0])])
  for name in names:
    sys.stdout.write('"{0}" '.format(name))
  print

def extract_macro_names(intended_for_inference):
  macro_names = []
  for macro in macros:
    if (macro.intended_for_inference() is intended_for_inference and
        hasattr(macro, 'name')):
      macro_names.append(macro.name)
  return sorted(macro_names)

def model_SPs():
  print_sorted_first_component(builtInSPsList)

def inference_SPs():
  print_sorted_first_component(inferenceSPsList)

def inference_prelude_SPs():
  print_sorted_first_component(inference_prelude.prelude)

def model_macros():
  for macro_name in extract_macro_names(False):
    sys.stdout.write('"{0}"'.format(macro_name))

def inference_macros():
  for macro_name in extract_macro_names(True):
    sys.stdout.write('"{0}"'.format(macro_name))

def callbacks():
  ripl = Lite().make_church_prime_ripl()
  print_sorted_first_component(ripl.sivm.core_sivm.engine.callbacks.iteritems())

def builtins():
  "All font lock level 3 builtins"
  print ";; model SP's"
  model_SPs()
  print ";; inference SP's"
  inference_SPs()
  print ";; inference prelude"
  inference_prelude_SPs()
  print ";; inference callbacks"
  callbacks()
  
def dispatch():
  return {"model_SPs": model_SPs,
          "inference_SPs": inference_SPs,
          "model_macros": model_macros,
          "inference_macros": inference_macros,
          "inference_prelude_SPs": inference_prelude_SPs,
          "callbacks": callbacks,
          "builtins": builtins}

if __name__ == "__main__":
  if len(sys.argv) == 1:
    print "Available arguments are: " + " ".join(dispatch().keys())
  else:
    arg = sys.argv[1]
    if arg in dispatch():
      dispatch()[arg]()
      print
    else:
      print "Bad keyword."
