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

# - Inputs and unconstrainable outputs are a list of 2-lists: name and type.
# - Constrainable outputs are a list of 3-lists: name, constrainable
#   name, type, and any number of size expressions.
# - A size expression is a string which, when evaluated in an
#   environment containing the inputs, gives the size in that
#   dimension.
#   - This is needed to be able to synthesize values.
# - An output that is not constrainable corresponds to a generated quantity
#   in Stan.
# - An output that is constrainable corresponds to a generated quantity
#   and an input datum, the latter named by the "constrainable name".
# - It is up to the user to make sure that the use as a constraint is
#   compatible with the generating process they define.
# - This maps to an SP with the given inputs and outputs, which is
#   likelihood-free on unconstrainable outputs, and has the Stan
#   parameters as (uncollapsed) latent state.
# - Temporary restriction: There can be only one output (because
#   Venture doesn't deal with primitive SPs that return multiple
#   outputs that are meant to be constrainable separately).

# Operating invariants:
# - Simulation has the inputs and simulates the parameters and the outputs
# - Log density has the inputs, outputs, and parameters, and evaluates
#   the posterior (of the parameters).
# - There is an AEKernel that has the inputs, outputs, and parameters, and
#   updates the parameters by taking a step.
# - Ergo, simulate needs to be able to synthesize bogus values for the
#   constrainable outputs

# Plan:
# - A model is represented as a made SP from inputs to outputs
# - made simulation makes an LSR (which need not carry any information)
# - simulating this lsr consists of sampling the parameters
#   conditioned on bogus data
# - given the result, (communicated via the aux), simulating the
#   output is straightforward (but needs bogus data again)
# - fiddling with the parameters now looks like a AEKernel, which
#   means I really need to be able to control when that gets run,
#   b/c it stands to be expensive
# - Nuts: The AEKernel is global to all applications, but I want
#   them to be independent :(

# Note: The mapping from inputs to parameters is not independently
# assessable in Stan; only the aggregate including the data is.

# Alternate plan (not implemented):
# - A made model is represented as a made SP from inputs to outputs,
#   that uses an ESR to cause the parameters to be simulated (by
#   another SP customized for the purpose)
# - Problem: The param SP can't properly absorb because it doesn't see
#   the data.  Could hack it by having it absorb with likelihood 1
#   every time, and leave the second SP responsible for absorbing
#   changes to the input at both the parameters and the data.
# - Problem: The param SP can't properly resimulate, even with a
#   kernel, because it doesn't see the data.

def interpret_type_spec(type_str):
  # TODO I should probably write a proper parser for type specs, or
  # else render the type language in Venture instead of evaling
  # user-supplied code like this.
  globals = {}
  exec "from venture.lite.types import *" in globals
  ans = eval(type_str, globals)
  return ans

def bogus_valid_value(_tp):
  return vv.VentureNumber(0) # TODO: Actually synthesize type-correct bogosity

def input_data_as_dict(input_spec, inputs):
  ans = dict([(k,v) for ((k,_), v) in zip(input_spec, inputs)])
  return ans

def output_spec_to_back_in_spec(output_spec):
  assert len(output_spec) == 1
  return [(output_spec[0][1], output_spec[0][2])]

def synthesize_bogus_data(c_output_spec, input_dict):
  assert len(c_output_spec) == 1
  name = c_output_spec[0][1]
  tp = interpret_type_spec(c_output_spec[0][2])
  input_dict = copy.copy(input_dict)
  sizes = [interpret_size(size, input_dict) for size in c_output_spec[0][3:]]
  ans = {name: synthesize_bogus_datum(tp, sizes)}
  return ans

def interpret_size(size, input_dict):
  return eval(size, input_dict)

def synthesize_bogus_datum(tp, sizes):
  # TODO This version ignores the type and just makes an array of the
  # desired shape.  Is that right?
  if len(sizes) == 0:
    return 0
  return [synthesize_bogus_datum(tp, sizes[1:]) for _ in range(sizes[0])]

def dict_as_output_data(output_spec, data):
  ans = [normalize_output_datum(data[output[0]]) for output in output_spec]
  return ans

def normalize_output_datum(datum):
  # Apparently the dimensionality of the numpy arrays that Stan emits
  # depends on the number of iterations done and the dimensionality of
  # the underlying datum.
  # - Apparently only with scalar-valued outputs, though.  Vector-valued
  #   ones do what I would expect.
  # - It also seems that with permuted=True, Stan squashes all the chains'
  #   outputs together.
  if len(datum.shape) == 0:
    return float(datum)
  else:
    return datum[0]

def cached_stan_model(model_code, cache_dir=None, **kwargs):
  if cache_dir is None:
    print "Not using Stan model cache"
    return pystan.StanModel(model_code=model_code, **kwargs)
  code_hash = hashlib.sha256(model_code).hexdigest()
  cache_file = 'compiled-stan-model-%s.pkl' % code_hash
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

def minimal_stan_run(model, **kwargs):
  """Create a StanFit object from a StanModel object.

Avoid moving the parameters from their initialization as much as possible."""
  # Apparently, pystan offers no way to completely avoid moving the
  # parameters:
  # https://github.com/stan-dev/pystan/issues/199
  # https://github.com/stan-dev/pystan/issues/200
  # For now, move a "small" amount (assuming the problem's geometry
  # has unit scale).
  control = {'adapt_engaged': False, 'stepsize': 1e-12, 'int_time': 1e-12,
             'stepsize_jitter': 0}
  ans = model.sampling(iter=1, chains=1, algorithm="HMC", control=control,
                       **kwargs)
  return ans

class MakerVenStanOutputPSP(DeterministicPSP):
  def simulate(self, args):
    (stan_prog, input_spec, c_output_spec) = args.operandValues()
    stan_model = cached_stan_model(stan_prog, cache_dir=".")
    the_sp = VenStanSP(stan_model, input_spec, c_output_spec)
    return VentureSPRecord(the_sp)

class VenStanSP(SP):
  def __init__(self, stan_model, input_spec, c_output_spec):
    args_types = [interpret_type_spec(itp) for _,itp in input_spec]
    assert len(c_output_spec) == 1
    output_type = interpret_type_spec(c_output_spec[0][2])
    self.f_type = SPType(args_types, output_type)
    req = TypedPSP(VenStanRequestPSP(), SPType(args_types, t.RequestType()))
    output = TypedPSP(VenStanOutputPSP(stan_model, input_spec, c_output_spec),
                      self.f_type)
    super(VenStanSP, self).__init__(req, output)
    self.stan_model = stan_model
    self.input_spec = input_spec
    self.c_output_spec = c_output_spec

  def synthesize_parameters_with_bogus_data(self, inputs):
    data_dict = input_data_as_dict(self.input_spec, inputs)
    data_dict.update(synthesize_bogus_data(self.c_output_spec, data_dict))
    fit = minimal_stan_run(self.stan_model, data=data_dict)
    return fit.extract()

  def update_parameters(self, inputs, params, outputs):
    second_input_spec = output_spec_to_back_in_spec(self.c_output_spec)
    data_dict = input_data_as_dict(self.input_spec, inputs)
    data_dict.update(input_data_as_dict(second_input_spec, outputs))
    # Setting the "thin" argument here has the effect that Stan
    # reports exactly one set of answers, which, by the magic of
    # Python being willing to treat a size-1 array as a scalar (!?)
    # makes the types of everything else work out.
    fit = self.stan_model.sampling(data=data_dict, iter=10, chains=1,
                                   warmup=5, thin=5, init=[params])
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
        inputs = self.f_type.unwrap_args(args).operandValues()
        params = self.synthesize_parameters_with_bogus_data(inputs)
        aux.applications[lsr] = (inputs, params, None)
    return 0

  def detachLatents(self, args, lsr, latentDB):
    aux = args.spaux()
    latentDB[lsr] = aux.applications[lsr]
    del aux.applications[lsr]
    return 0

  def hasAEKernel(self): return True

  def AEInfer(self, aux):
    for lsr, (inputs, params, output) in aux.applications.iteritems():
      new_params = self.update_parameters(inputs, params, [output])
      aux.applications[lsr] = (inputs, new_params, output)

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
  def __init__(self, stan_model, input_spec, c_output_spec):
    self.stan_model = stan_model
    self.input_spec = input_spec
    self.c_output_spec = c_output_spec

  def compute_generated_quantities_from_bogus_data(self, inputs, params):
    data_dict = input_data_as_dict(self.input_spec, inputs)
    data_dict.update(synthesize_bogus_data(self.c_output_spec, data_dict))
    fit = minimal_stan_run(self.stan_model, data=data_dict, init=[params])
    return dict_as_output_data(self.c_output_spec, fit.extract())

  def evaluate_posterior(self, inputs, params, outputs):
    print "Evaluating", inputs, params, outputs
    second_input_spec = output_spec_to_back_in_spec(self.c_output_spec)
    data_dict = input_data_as_dict(self.input_spec, inputs)
    data_dict.update(input_data_as_dict(second_input_spec, outputs))
    fit = minimal_stan_run(self.stan_model, data=data_dict, init=[params])
    upars = fit.unconstrain_pars(params)
    ans = fit.log_prob(upars)
    print "Evaluated posterior", ans
    return ans

  def simulate(self, args):
    inputs = args.operandValues()
    (_, params, _) = args.spaux().applications[args.node.requestNode]
    outputs = self.compute_generated_quantities_from_bogus_data(inputs, params)
    return outputs[0]

  def logDensity(self, value, args):
    inputs = args.operandValues()
    (_, params, _) = args.spaux().applications[args.node.requestNode]
    return self.evaluate_posterior(inputs, params, [value])

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
                t.HomogeneousListType(t.HomogeneousListType(t.StringType()))]
  the_sp = sp.typed_nr(MakerVenStanOutputPSP(),
                       args_types,
                       t.AnyType("SP representing the Stan model"))
  ripl.bind_foreign_sp("make_ven_stan", the_sp)
