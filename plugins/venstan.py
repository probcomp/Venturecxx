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

import copy
import cPickle as pickle
import hashlib
import os

import pystan

from venture.lite.psp import DeterministicPSP
from venture.lite.psp import RandomPSP
from venture.lite.psp import TypedPSP
from venture.lite.request import Request
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord

import venture.lite.sp_help as sp
import venture.lite.types as t
import venture.lite.value as vv

# - Inputs are a list of 2-lists: name and type.
# - Output are a list of 3-lists: name, type, and constrainable name which may be Nil.
# - An output that is not constrainable corresponds to a generated quantity
#   in Stan.
# - An output that is constrainable corresponds to a generated quantity
#   and an input datum, the latter named by the "constrainable name".
# - It is up to the user to make sure that the use as a constraint is
#   compatible with the generating process they define.
# - This all produces an SP with the given inputs and outputs, which
#   is likelihood-free on unconstrainable outputs, and has the Stan
#   parameters as (uncollapsed) latent state.

# Operating invariants:
# - Simulation has the inputs and simulates the parameters and the outputs
# - Log density has the inputs, outputs, and parameters, and evaluates
#   the posterior (?) (likelihood only?)
# - There is an LKernel that has the inputs, outputs, and parameters, and
#   updates the parameters by taking a step
#   - Can I have an interface for taking multiple steps in batch?
#   - Can I have an interface for running to convergence?
#   - What do I do with the unconstrainable outputs?  They need to be
#     resampled, without resampling the constrainable ones.
# - Ergo, simulate needs to be able to synthesize bogus values for the
#   constrainable outputs

# Plan:
# - A model is represented as a made SP from inputs to outputs
# - made simulation makes an LSR (which need not carry any information)
# - simulating this lsr consists of sampling the parameters
#   conditioned on bogus data
# - given the result, (communicated via the aux, presumably),
#   simulating the output is straightforward (but needs bogus data)
# - fiddling with the parameters now looks like a AEKernel, which
#   means I really need to be able to control when that gets run,
#   b/c it stands to be expensive
# - Nuts: The AEKernel is global to all applications, but I want
#   them to be independent :(

# Thought: Is it reasonable to use primitive multivalue returns to
# separate constrainable from unconstrainable outputs?

# Problem: There is no way to incorporate downstream uses of the
# generated quantities and/or parameters into the behavior of the Stan
# simulator.

# Oddly, simulateLatents doesn't get the Args struct.  Perhaps the
# intention is that the requester can pass all pertinent information
# along.

# Note: The mapping from inputs to parameters is not independently
# assessable in Stan; only the aggregate including the data is.

# The request PSP can't both extract values into the lsr and assess at
# the same time.  Could do nodes, or could do an ESR for a custom SP.
# - Problem: The SP can't properly extract values from the nodes when
#   simulating the latent, because it doesn't have a pointer to the
#   trace (which is necessary to respect the particles hack).

# Solution: give simulateLatents the Args corresponding to the
# application in question.
# - May have the side effect of simplifying other uses of
#   simulateLatents, but maybe not.
# - HMM seems to be the only other SP that uses latent simulation
#   requests?

# Alternate plan:
# - A made model is represented as a made SP from inputs to outputs,
#   that uses an ESR to cause the parameters to be simulated (by
#   another SP customized for the purpose)
# - Problem: The param SP can't properly absorb because it doesn't see
#   the data.  Could hack it by having it absorb with likelihood 1
#   every time, and leave the second SP responsible for absorbing
#   changes to the input at both the parameters and the data.
# - Problem: The param SP can't properly resimulate, even with a
#   kernel, because it doesn't see the data.

def interpret_type_spec(_tp):
  return t.NumberType() # TODO: Actually interpret types

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

def bogus_valid_value(_tp):
  return vv.VentureNumber(0) # TODO: Actually synthesize type-correct bogosity

def input_data_as_dict(input_spec, inputs):
  return {}

def synthesize_bogus_data(output_spec):
  return {}

def dict_as_output_data(output_spec, data):
  return 0

def cached_stan_model(model_code, cache_dir=None, **kwargs):
  if cache_dir is None:
    print "Not using Stan model cache"
    return pystan.StanModel(model_code=model_code, **kwargs)
  code_hash = hashlib.sha256(model_code).hexdigest()
  cache_file = 'compiled-model-%s.pkl' % code_hash
  cache_path = os.path.join(cache_dir, cache_file)
  try:
    model = pickle.load(open(cache_path, 'rb'))
    print "Loaded model from cache %s" % cache_file
  except:
    model = pystan.StanModel(model_code=model_code, **kwargs)
    with open(cache_path, 'wb') as f:
      pickle.dump(model, f)
      print "Saved model to cache %s" % cache_file
  return model

class BogusModelFit(object):
  """Trick the PyStan API into accepting a model that was compiled but never run

as a "Fit" for purposes of avoiding recompilation."""
  def __init__(self, model):
    self.stanmodel = model

class MakerVenStanOutputPSP(DeterministicPSP):
  def simulate(self, args):
    (stan_prog, input_spec, param_spec, output_spec) = args.operandValues()
    built_result = cached_stan_model(stan_prog, cache_dir=".")
    the_sp = VenStanSP(BogusModelFit(built_result),
                       input_spec, param_spec, output_spec)
    return VentureSPRecord(the_sp)

class VenStanSP(SP):
  def __init__(self, built_result, input_spec, param_spec, output_spec):
    (args_types, output_type) = io_spec_to_type_spec(input_spec, output_spec)
    req = TypedPSP(VenStanRequestPSP(), SPType(args_types, t.RequestType()))
    output = TypedPSP(VenStanOutputPSP(built_result,
                                       input_spec, param_spec, output_spec),
                      SPType(args_types, output_type))
    super(VenStanSP, self).__init__(req, output)
    self.built_result = built_result
    self.input_spec = input_spec
    self.output_spec = output_spec

  def synthesize_parameters_with_bogus_data(self, inputs):
    data_dict = input_data_as_dict(self.input_spec, inputs)
    data_dict.update(synthesize_bogus_data(self.output_spec))
    fit = pystan.stan(fit=self.built_result, data=data_dict, iter=1, chains=1, verbose=True)
    print fit.extract()
    # print fit Dies in trying to compute the effective sample size?
    return fit.extract()

  def update_parameters(self, inputs, params, outputs):
    data_dict = input_data_as_dict(self.input_spec, inputs)
    data_dict.update(input_data_as_dict(self.output_spec, outputs))
    fit = pystan.stan(fit=self.built_result, data=data_dict, iter=10, chains=1,
                      init=[params])
    print fit.extract()
    return fit.extract()

  def constructSPAux(self): return VenStanSPAux()

  def constructLatentDB(self):
    # { app_id => (inputs, parameters, outputs) }
    return {}

  def simulateLatents(self, args, lsr, shouldRestore, latentDB):
    aux = args.spaux()
    if lsr not in aux.applications:
      if shouldRestore:
        aux.applications[lsr] = latentDB[lsr]
      else:
        inputs = args.operandValues()
        params = self.synthesize_parameters_with_bogus_data(inputs)
        aux.applications[lsr] = (inputs, params, None)
    return 0

  def detachLatents(self, args, lsr, latentDB):
    aux = args.spaux()
    latentDB[lsr] = aux.applications[lsr]
    del aux[lsr]
    return 0

  def hasAEKernel(self): return True

  def AEInfer(self, aux):
    for lsr, (inputs, params, outputs) in aux.applications.iteritems():
      new_params = self.update_parameters(inputs, params, outputs)
      aux[lsr] = (inputs, new_params, outputs)

# The Aux is shared across all applications, so I use a dictionary
# with unique keys to implement independence.
class VenStanSPAux(SPAux):
  def __init__(self):
    super(VenStanSPAux,self).__init__()
    self.applications = {} # { node -> (inputs, params, Maybe outputs) }

  def copy(self):
    ans = VenStanSPAux()
    ans.applications = copy.copy(self.applications)
    return ans

class VenStanRequestPSP(DeterministicPSP):
  def simulate(self, args):
    # The args node uniquely identifies the application
    return Request([], [args.node])
  def gradientOfSimulate(self, args, _value, _direction):
    return [0 for _ in args.operandNodes]
  def canAbsorb(self, _trace, _appNode, _parentNode):
    return True

class VenStanOutputPSP(RandomPSP):
  def __init__(self, stan_model, input_spec, param_spec, output_spec):
    self.stan_model = stan_model
    self.input_spec = input_spec
    self.param_spec = param_spec
    self.output_spec = output_spec
    (self.input_names, self.output_names) = io_spec_to_api_spec(input_spec, output_spec)

  def compute_generated_quantities_from_bogus_data(self, inputs, params):
    data_dict = input_data_as_dict(self.input_spec, inputs)
    data_dict.update(synthesize_bogus_data(self.output_spec))
    fit = pystan.stan(fit=self.stan_model, data=data_dict, iter=1, chains=1,
                      init=[params])
    print fit.extract()
    return dict_as_output_data(self.output_spec, fit.extract())

  def evaluate_posterior(self, inputs, params, outputs):
    data_dict = input_data_as_dict(self.input_spec, inputs)
    data_dict.update(input_data_as_dict(self.output_spec, outputs))
    param_dict = input_data_as_dict(self.param_spec, params)
    fit = pystan.stan(fit=self.stan_model, data=data_dict, iter=0, chains=1,
                      init=[param_dict])
    ans = fit.log_prob(param_dict) # TODO Transform the parameters
    print fit, ans
    return ans

  def simulate(self, args):
    inputs = args.operandValues()
    (_, params, _) = args.spaux().applications[args.node.requestNode]
    outputs = self.compute_generated_quantities_from_bogus_data(inputs, params)
    return outputs

  def logDensity(self, value, args):
    inputs = args.operandValues()
    (_, params, _) = args.spaux().applications[args.node.requestNode]
    return self.evaluate_posterior(inputs, params, value)

  def incorporate(self, value, args):
    inputs = args.operandValues()
    aux = args.spaux()
    (_, params, _) = aux.applications[args.node.requestNode]
    aux.applications[args.node.requestNode] = (inputs, params, value)

  def unincorporate(self, value, args):
    aux = args.spaux()
    (inputs, params, _) = aux.applications[args.node.requestNode]
    aux.applications[args.node.requestNode] = (inputs, params, None)

def __venture_start__(ripl):
  args_types = [t.StringType(),
                t.HomogeneousListType(t.HomogeneousListType(t.StringType())),
                t.HomogeneousListType(t.HomogeneousListType(t.StringType())),
                t.HomogeneousListType(t.HomogeneousListType(t.StringType()))]
  the_sp = sp.typed_nr(MakerVenStanOutputPSP(),
                       args_types,
                       t.AnyType("SP representing the Stan model"))
  ripl.bind_foreign_sp("make_ven_stan", the_sp)
