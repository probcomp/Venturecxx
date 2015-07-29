# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

from sp import SPType

from sp_registry import registerBuiltinSP, builtInSPs, builtInSPsIter # Importing for re-export pylint:disable=unused-import

import value as v
import types as t
from utils import raise_
from exception import VentureValueError

from sp_help import *

# These modules actually define the PSPs.
import venmath
import basic_sps
import vectors
import functional
import conditionals
import csp
import eval_sps
import msp
import scope
import discrete
import dirichlet
import continuous
import crp
import hmm
import cmvn
import function
import gp

# The types in the types module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False), "nil" : v.VentureNil() }

def debug_print(label, value):
  print 'debug ' + label + ': ' + str(value)
  return value

generic_normal = dispatching_psp(
  [SPType([t.NumberType(), t.NumberType()], t.NumberType()), # TODO Sigma is really non-zero, but negative is OK by scaling
   SPType([t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType()))],
  [continuous.NormalOutputPSP(), continuous.NormalsvOutputPSP(),
   continuous.NormalvsOutputPSP(), continuous.NormalvvOutputPSP()])

registerBuiltinSP("debug",
                  deterministic_typed(debug_print, [t.SymbolType(), t.AnyType("k")], t.AnyType("k"),
                                      descr = "Print the given value, labeled by a Symbol. Return the value. Intended for debugging or for monitoring execution."))


registerBuiltinSP("zip", deterministic_typed(zip, [t.ListType()], t.HomogeneousListType(t.ListType()), variadic=True,
                                             descr="zip returns a list of lists, where the i-th nested list contains the i-th element from each of the input arguments"))

registerBuiltinSP("binomial", typed_nr(discrete.BinomialOutputPSP(),
                                       [t.CountType(), t.ProbabilityType()], t.CountType()))
registerBuiltinSP("flip", typed_nr(discrete.BernoulliOutputPSP(),
                                   [t.ProbabilityType()], t.BoolType(), min_req_args=0))
registerBuiltinSP("bernoulli", typed_nr(discrete.BernoulliOutputPSP(),
                                        [t.ProbabilityType()], t.IntegerType(), min_req_args=0))
registerBuiltinSP("log_flip", typed_nr(discrete.LogBernoulliOutputPSP(),
                                       [t.NumberType()], t.BoolType()))
registerBuiltinSP("log_bernoulli", typed_nr(discrete.LogBernoulliOutputPSP(), [t.NumberType()], t.BoolType()))
registerBuiltinSP("categorical", typed_nr(discrete.CategoricalOutputPSP(),
                                          [t.SimplexType(), t.ArrayType()], t.AnyType(), min_req_args=1))
registerBuiltinSP("uniform_discrete", typed_nr(discrete.UniformDiscreteOutputPSP(),
                                               [t.IntegerType(), t.IntegerType()], t.IntegerType()))
registerBuiltinSP("poisson", typed_nr(discrete.PoissonOutputPSP(), [t.PositiveType()], t.CountType()))
registerBuiltinSP("normal", no_request(generic_normal))
registerBuiltinSP("vonmises", typed_nr(continuous.VonMisesOutputPSP(),
                                       [t.NumberType(), t.PositiveType()], t.NumberType()))
registerBuiltinSP("uniform_continuous",typed_nr(continuous.UniformOutputPSP(),
                                                [t.NumberType(), t.NumberType()], t.NumberType()))
registerBuiltinSP("beta", typed_nr(continuous.BetaOutputPSP(),
                                   [t.PositiveType(), t.PositiveType()], t.ProbabilityType()))
registerBuiltinSP("expon", typed_nr(continuous.ExponOutputPSP(),
                                    [t.PositiveType()], t.PositiveType()))
registerBuiltinSP("gamma", typed_nr(continuous.GammaOutputPSP(),
                                    [t.PositiveType(), t.PositiveType()], t.PositiveType()))
registerBuiltinSP("student_t", typed_nr(continuous.StudentTOutputPSP(),
                                        [t.PositiveType(), t.NumberType(), t.NumberType()],
                                        t.NumberType(), min_req_args=1 ))
registerBuiltinSP("inv_gamma", typed_nr(continuous.InvGammaOutputPSP(),
                                        [t.PositiveType(), t.PositiveType()], t.PositiveType()))
registerBuiltinSP("laplace", typed_nr(continuous.LaplaceOutputPSP(),
                                      [t.NumberType(), t.PositiveType()], t.NumberType()))

registerBuiltinSP("multivariate_normal", typed_nr(continuous.MVNormalOutputPSP(),
                                                  [t.HomogeneousArrayType(t.NumberType()), t.SymmetricMatrixType()],
                                                  t.HomogeneousArrayType(t.NumberType())))
registerBuiltinSP("inv_wishart", typed_nr(continuous.InverseWishartPSP(),
                                          [t.SymmetricMatrixType(), t.PositiveType()], t.SymmetricMatrixType()))
registerBuiltinSP("wishart", typed_nr(continuous.WishartPSP(),
                                      [t.SymmetricMatrixType(), t.PositiveType()], t.SymmetricMatrixType()))

registerBuiltinSP("make_beta_bernoulli", typed_nr(discrete.MakerCBetaBernoulliOutputPSP(),
                                                  [t.PositiveType(), t.PositiveType()], SPType([], t.BoolType())))
registerBuiltinSP("make_uc_beta_bernoulli", typed_nr(discrete.MakerUBetaBernoulliOutputPSP(),
                                                     [t.PositiveType(), t.PositiveType()], SPType([], t.BoolType())))
registerBuiltinSP("make_suff_stat_bernoulli", typed_nr(discrete.MakerSuffBernoulliOutputPSP(),
                                                       [t.NumberType()], SPType([], t.BoolType())))

registerBuiltinSP("dirichlet", typed_nr(dirichlet.DirichletOutputPSP(),
                                        [t.HomogeneousArrayType(t.PositiveType())], t.SimplexType()))
registerBuiltinSP("symmetric_dirichlet", typed_nr(dirichlet.SymmetricDirichletOutputPSP(),
                                                  [t.PositiveType(), t.CountType()], t.SimplexType()))

registerBuiltinSP("make_dir_mult",
                  typed_nr(dirichlet.MakerCDirMultOutputPSP(),
                           [t.HomogeneousArrayType(t.PositiveType()), t.ArrayType()],
                           SPType([], t.AnyType()), min_req_args=1))
registerBuiltinSP("make_uc_dir_mult",
                  typed_nr(dirichlet.MakerUDirMultOutputPSP(),
                           [t.HomogeneousArrayType(t.PositiveType()), t.ArrayType()],
                           SPType([], t.AnyType()), min_req_args=1))

registerBuiltinSP("make_sym_dir_mult",
                  typed_nr(dirichlet.MakerCSymDirMultOutputPSP(),
                           [t.PositiveType(), t.CountType(), t.ArrayType()],
                           # Saying AnyType here requires the underlying psp to emit a VentureValue.
                           SPType([], t.AnyType()), min_req_args=2))

registerBuiltinSP("make_uc_sym_dir_mult",
                  typed_nr(dirichlet.MakerUSymDirMultOutputPSP(),
                           [t.PositiveType(), t.CountType(), t.ArrayType()],
                           SPType([], t.AnyType()), min_req_args=2))

registerBuiltinSP("make_gp", gp.makeGPSP)
registerBuiltinSP("apply_function", function.applyFunctionSP)
registerBuiltinSP("exactly", typed_nr(discrete.ExactlyOutputPSP(),
                                      [t.AnyType(), t.NumberType()], t.AnyType(), min_req_args=1))
registerBuiltinSP("value_error", deterministic_typed(lambda s: raise_(VentureValueError(str(s))),
                                                     [t.AnyType()], t.AnyType()))
