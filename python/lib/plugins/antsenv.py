# Copyright (c) 2015, 2016 MIT Probabilistic Computing Project.
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

from functools import partial

from venture.plugins.venstan import (
  t, sp, DeterministicPSP, cached_stan_model,
  VentureSPRecord,
  SP, SPType,
  TypedPSP,
  SPAux, RandomPSP,
  copy,
)
from venture.lite.psp import NullRequestPSP
import venture.lite.value as v

def applications_as_data_dict(spec, applications):
  (count_name, input_names, output_name) = spec
  data_dict = {}
  data_dict[count_name] = len(applications)
  for name in input_names:
    data_dict[name] = []
  data_dict[output_name] = []
  for (inputs, output) in applications.values():
    for name, value in zip(input_names, inputs):
      data_dict[name].append(value)
    data_dict[output_name].append(output)
  return data_dict

class MakerVenStanOutputPSP(DeterministicPSP):
  def simulate(self, args):
    vals = args.operandValues()
    (stan_program, count_name, input_names, output_name) = vals
    # TODO take these as optional arguments
    cache_dir = "."
    input_types = [t.NumberType() for _ in input_names]
    output_type = t.NumberType()
    # input_types = [interpret_type_spec(itp) for itp in input_spec]
    # output_type = interpret_type_spec(output_spec)
    stan_model = cached_stan_model(stan_program, cache_dir=cache_dir)
    the_sp = VenStanSP(stan_model, count_name, input_names, output_name,
                       input_types, output_type)
    return VentureSPRecord(the_sp)

class VenStanSP(SP):
  def __init__(self, stan_model, count_name,
               input_names, output_name,
               input_types, output_type):
    req = NullRequestPSP()
    output = TypedPSP(VenStanOutputPSP(stan_model),
                      SPType(input_types, output_type))
    super(VenStanSP, self).__init__(req, output)
    self.stan_model = stan_model
    self.spec = (count_name, input_names, output_name)

  def constructSPAux(self): return VenStanSPAux()

  def hasAEKernel(self): return True

  def show(self, aux):
    return partial(self.infer, aux)

  def infer(self, aux, iter=2000, warmup=None, **kwargs):
    data_dict = applications_as_data_dict(self.spec, aux.applications)
    if warmup is None:
      warmup = iter//2  # PyStan default
    # Setting the "thin" argument here has the effect that Stan
    # reports exactly one set of answers, which, by the magic of
    # Python being willing to treat a size-1 array as a scalar (!?)
    # makes the types of everything else work out.
    thin = iter - warmup
    if aux.parameters is not None:
      init = [aux.parameters]
    else:
      init = 'random'
    fit = self.stan_model.sampling(data=data_dict, iter=iter, warmup=warmup,
                                   chains=1, thin=thin, init=init)
    aux.parameters = fit.extract()

class VenStanSPAux(SPAux):
  def __init__(self):
    super(VenStanSPAux,self).__init__()
    self.applications = {} # { node -> (inputs, output) }
    self.parameters = None

  def copy(self):
    ans = VenStanSPAux()
    ans.applications = copy.copy(self.applications)
    return ans

  def asVentureValue(self):
    if self.parameters is None:
      return v.VentureNil()
    else:
      return v.VentureDict({
        v.VentureString(key): v.VentureString(str(val))
        for (key, val) in self.parameters.items()
      })

class VenStanOutputPSP(RandomPSP):
  def __init__(self, stan_model):
    self.stan_model = stan_model

  def simulate(self, _args):
    # return some bogus value, unless generated quantities are defined
    return 0

  def logDensity(self, _value, _args):
    # return some bogus value, unless generated quantities are defined
    return 0

  def incorporate(self, value, args):
    inputs = args.operandValues()
    aux = args.spaux()
    aux.applications[args.node] = (inputs, value)

  def unincorporate(self, value, args):
    aux = args.spaux()
    del aux.applications[args.node]

def __venture_start__(ripl):
  args_types = [
      t.StringType("Stan program"),
      t.StringType("count variable name"),
      t.HomogeneousArrayType(t.StringType("input variable names")),
      t.StringType("output variable name"),
  ]
  the_sp = sp.typed_nr(MakerVenStanOutputPSP(),
                       args_types,
                       t.AnyType("SP representing the Stan model"),
                       min_req_args=4)
  ripl.bind_foreign_sp("make_ven_stan", the_sp)
