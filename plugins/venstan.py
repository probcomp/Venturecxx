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

import pystan

from venture.lite.psp import DeterministicPSP
from venture.lite.psp import RandomPSP
from venture.lite.sp_help import typed_nr
from venture.lite.sp import VentureSPRecord

import venture.lite.types as t

# - Inputs are a list of pairs: name and type.
# - Output are a list of triples: name, type, and constrainable name which may be Nil.
# - An output that is not constrainable corresponds to a generated quantity
#   in Stan.
# - An output that is constrainable corresponds to a generated quantity
#   and an input datum, the latter named by the "constrainable name".
# - It is up to the user to make sure that the use as a constraint is
#   compatible with the generating process they define.
# - This all produces an SP with the given inputs and outputs, which
#   is likelihood-free on unconstrainable outputs, and has the Stan
#   parameters as (uncollapsed) latent state.

def interpret_type_spec(_tp):
  return t.NumberType()

def io_spec_to_type_spec(inputs, outputs):
  assert len(outputs) == 1
  (_, tp, _) = outputs[0]
  return ([interpret_type_spec(tp) for _,tp in inputs],
          interpret_type_spec(tp))

def io_spec_to_api_spec(inputs, outputs):
  assert len(outputs) == 1
  (name, _, observable_name) = outputs[0]
  output_names = [name]
  input_names = [name for name,_ in inputs]
  if observable_name is not None:
    input_names.append(observable_name)
  return (input_names, output_names)

class MakerVenStanOutputPSP(DeterministicPSP):
  def simulate(self, args):
    (stan_prog, inputs, outputs) = args.operandValues()
    (args_types, output_type) = io_spec_to_type_spec(inputs, outputs)
    built_result = pystan.stanc(model_code=stan_prog)
    psp = VenStanOutputPSP(built_result, inputs, outputs)
    sp = typed_nr(psp, args_types, output_type)
    return VentureSPRecord(sp)

class VenStanOutputPSP(RandomPSP):
  def __init__(self, stan_model, inputs, outputs):
    self.stan_model = stan_model
    (self.input_names, self.output_names) = io_spec_to_api_spec(inputs, outputs)

  def simulate(self, args):
    pass
