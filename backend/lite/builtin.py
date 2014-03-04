import math
import numpy as np

from sp import VentureSP
from psp import NullRequestPSP, ESRRefOutputPSP, PSP, TypedPSP

import discrete
import continuous
import dstructures
import csp
import crp
import msp
import hmm
import conditionals
import scope
import eval_sps
import value as v
import env

# The types in the value module are generated programmatically, so
# pylint doesn't find out about them.
# pylint: disable=no-member

def builtInValues():
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False) }

def no_request(output): return VentureSP(NullRequestPSP(), output)

def typed_nr(output, args_types, return_type, **kwargs):
  return no_request(TypedPSP(args_types, return_type, output, **kwargs))

def deterministic_psp(f, descr=None):
  class DeterministicPSP(PSP):
    def __init__(self, descr):
      self.descr = descr
      if self.descr is None:
        self.descr = "deterministic %s"
    def simulate(self,args):
      return f(*args.operandValues)
    def description(self,name):
      return self.descr % name
  return DeterministicPSP(descr)

def deterministic(f, descr=None):
  return no_request(deterministic_psp(f, descr))

def deterministic_typed(f, args_types, return_type, descr=None, **kwargs):
  return typed_nr(deterministic_psp(f, descr), args_types, return_type, **kwargs)

def binaryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType(), v.NumberType()], v.NumberType(), descr=descr)

def binaryNumS(output):
  return typed_nr(output, [v.NumberType(), v.NumberType()], v.NumberType())

def unaryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), descr=descr)

def unaryNumS(f):
  return typed_nr(f, [v.NumberType()], v.NumberType())

def naryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), variadic=True, descr=descr)

def type_test(t):
  return deterministic(lambda thing: v.VentureBool(thing in t),
                       "%s :: <SP <object> -> <bool>>\nReturns true iff its argument is a " + t.name())

def builtInSPsList():
  return [ [ "plus",  naryNum(lambda *args: sum(args),
                              "%s returns the sum of all its arguments") ],
           [ "minus", binaryNum(lambda x,y: x - y,
                                "%s returns the difference between its first and second arguments") ],
           [ "times", naryNum(lambda *args: reduce(lambda x,y: x * y,args,1),
                              "%s returns the product of all its arguments") ],
           [ "div",   binaryNum(lambda x,y: x / y,
                                "%s returns the quotient of its first argument by its second") ],
           [ "eq",    deterministic(lambda x,y: v.VentureBool(x.compare(y) == 0),
                                    "%s :: <SP <object> <object> -> <bool>>\nCompares its two arguments for equality") ],
           [ "gt",    deterministic(lambda x,y: v.VentureBool(x.compare(y) >  0),
                                    "%s :: <SP <object> <object> -> <bool>>\nReturns true if its first argument compares greater than its second") ],
           [ "gte",   deterministic(lambda x,y: v.VentureBool(x.compare(y) >= 0),
                                    "%s :: <SP <object> <object> -> <bool>>\nReturns true if its first argument compares greater than or equal to its second") ],
           [ "lt",    deterministic(lambda x,y: v.VentureBool(x.compare(y) <  0),
                                    "%s :: <SP <object> <object> -> <bool>>\nReturns true if its first argument compares less than its second") ],
           [ "lte",   deterministic(lambda x,y: v.VentureBool(x.compare(y) <= 0),
                                    "%s :: <SP <object> <object> -> <bool>>\nReturns true if its first argument compares less than or equal to its second") ],
           # Only makes sense with VentureAtom/VentureNumber distinction
           [ "real",  deterministic_typed(lambda x:x, [v.AtomType()], v.NumberType(),
                                          "%s returns the identity of its argument atom as a number") ],
           [ "atom_eq", deterministic_typed(lambda x,y: x == y, [v.AtomType(), v.AtomType()], v.BoolType(),
                                            "%s tests its two arguments, which must be atoms, for equality") ],

           [ "sin", unaryNum(math.sin, "Returns the %s of its argument") ],
           [ "cos", unaryNum(math.cos, "Returns the %s of its argument") ],
           [ "tan", unaryNum(math.tan, "Returns the %s of its argument") ],
           [ "hypot", binaryNum(math.hypot, "Returns the %s of its arguments") ],
           [ "exp", unaryNum(math.exp, "Returns the %s of its argument") ],
           [ "log", unaryNum(math.log, "Returns the %s of its argument") ],
           [ "pow", binaryNum(math.pow, "%s returns its first argument raised to the power of its second argument") ],
           [ "sqrt", unaryNum(math.sqrt, "Returns the %s of its argument") ],

           [ "not", deterministic_typed(lambda x: not x, [v.BoolType()], v.BoolType(),
                                        "%s returns the logical negation of its argument") ],

           [ "is_symbol", type_test(v.SymbolType()) ],
           [ "is_atom", type_test(v.AtomType()) ],

           [ "list", deterministic(v.pythonListToVentureList,
                                   "%s :: <SP <object> ... -> <list>>\nReturns the list of its arguments") ],
           [ "pair", deterministic(v.VenturePair,
                                   "%s :: <SP <object> <object> -> <pair>>\nReturns the pair whose first component is the first argument and whose second component is the second argument") ],
           [ "is_pair", type_test(v.PairType()) ],
           [ "first", deterministic_typed(lambda p: p[0], [v.PairType()], v.AnyType(),
                                          "%s returns the first component of its argument pair") ],
           [ "rest", deterministic_typed(lambda p: p[1], [v.PairType()], v.AnyType(),
                                         "%s returns the second component of its argument pair") ],
           [ "second", deterministic_typed(lambda p: p[1].first, [v.PairType()], v.AnyType(),
                                           "%s returns the first component of the second component of its argument") ],

           [ "map_list",VentureSP(dstructures.MapListRequestPSP(),dstructures.MapListOutputPSP()) ],

           [ "array", deterministic(lambda *args: v.VentureArray(np.array(args)),
                                    "%s :: <SP <object> ... -> <array>>\nReturns an array initialized with its arguments") ],
           [ "is_array", type_test(v.ArrayType()) ],
           [ "dict", no_request(dstructures.DictOutputPSP()) ],
           [ "is_dict", type_test(v.DictType()) ],
           [ "matrix", deterministic(lambda rows: v.VentureMatrix(np.mat([[val.getNumber() for val in row.asPythonList()] for row in rows.asPythonList()])),
                                     "%s :: <SP <list <list a>> -> <matrix a>>\nReturns a matrix formed from the given list of rows.  It is an error if the given list is not rectangular.") ],
           [ "is_matrix", type_test(v.MatrixType()) ],
           [ "simplex", deterministic_typed(lambda *nums: np.array(nums), [v.NumberType()], v.SimplexType(), variadic=True,
                                            descr="%s returns the simplex point given by its argument coordinates.") ],
           [ "is_simplex", type_test(v.SimplexType()) ],

           [ "lookup", deterministic(lambda xs, x: xs.lookup(x),
                                     descr="%s :: <SP <mapping k v> k -> v>\nLooks the given key up in the given mapping and returns the result.  It is an error if the key is not in the mapping.  Lists and arrays are viewed as mappings from indices to the corresponding elements.") ],
           [ "contains", deterministic(lambda xs, x: v.VentureBool(xs.contains(x)),
                                       "%s :: <SP <mapping k v> k -> <bool>>\nReports whether the given key appears in the given mapping or not.") ],
           [ "size", deterministic(lambda xs: v.VentureNumber(xs.size()),
                                   "%s :: <SP <collection> -> <number>>\nReturns the number of elements in the given collection") ],

           [ "branch", VentureSP(conditionals.BranchRequestPSP(),ESRRefOutputPSP()) ],
           [ "biplex", deterministic_typed(lambda p, c, a: c if p else a, [v.BoolType(), v.AnyType(), v.AnyType()], v.AnyType())],
           [ "make_csp", no_request(csp.MakeCSPOutputPSP()) ],

           [ "get_current_environment",no_request(eval_sps.GetCurrentEnvOutputPSP()) ],
           [ "get_empty_environment",no_request(eval_sps.GetEmptyEnvOutputPSP()) ],
           [ "is_environment", type_test(env.EnvironmentType()) ],
           [ "extend_environment",no_request(eval_sps.ExtendEnvOutputPSP()) ],
           [ "eval",VentureSP(eval_sps.EvalRequestPSP(),ESRRefOutputPSP()) ],

           [ "mem",no_request(msp.MakeMSPOutputPSP()) ],

           [ "scope_include",no_request(scope.ScopeIncludeOutputPSP()) ],

           [ "binomial", binaryNumS(discrete.BinomialOutputPSP()) ],
           [ "flip", typed_nr(discrete.BernoulliOutputPSP(), [v.NumberType()], v.BoolType(), min_req_args=0) ],
           [ "bernoulli", typed_nr(discrete.BernoulliOutputPSP(), [v.NumberType()], v.BoolType(), min_req_args=0) ],
           [ "categorical", typed_nr(discrete.CategoricalOutputPSP(), [v.SimplexType(), v.ArrayType()], v.AnyType(), min_req_args=1) ],

           [ "normal",binaryNumS(continuous.NormalOutputPSP()) ],
           [ "uniform_continuous",binaryNumS(continuous.UniformOutputPSP()) ],
           [ "beta",binaryNumS(continuous.BetaOutputPSP()) ],
           [ "gamma",binaryNumS(continuous.GammaOutputPSP()) ],
           [ "student_t",unaryNumS(continuous.StudentTOutputPSP()) ],

           [ "dirichlet",typed_nr(discrete.DirichletOutputPSP(), [v.HomogeneousArrayType(v.NumberType())], v.SimplexType()) ],
           [ "symmetric_dirichlet",typed_nr(discrete.SymmetricDirichletOutputPSP(), [v.NumberType(), v.NumberType()], v.SimplexType()) ],

           [ "make_dir_mult",typed_nr(discrete.MakerCDirMultOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.ArrayType()], v.AnyType(), min_req_args=1) ],
           [ "make_uc_dir_mult",typed_nr(discrete.MakerUDirMultOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.ArrayType()], v.AnyType(), min_req_args=1) ],

           [ "make_sym_dir_mult",typed_nr(discrete.MakerCSymDirMultOutputPSP(), [v.NumberType(), v.NumberType(), v.ArrayType()], v.AnyType(), min_req_args=2) ], # Saying AnyType here requires the underlying psp to emit a VentureValue.
           [ "make_uc_sym_dir_mult",typed_nr(discrete.MakerUSymDirMultOutputPSP(), [v.NumberType(), v.NumberType(), v.ArrayType()], v.AnyType(), min_req_args=2) ],

           [ "make_beta_bernoulli",typed_nr(discrete.MakerCBetaBernoulliOutputPSP(), [v.NumberType(), v.NumberType()], v.AnyType()) ],
           [ "make_uc_beta_bernoulli",typed_nr(discrete.MakerUBetaBernoulliOutputPSP(), [v.NumberType(), v.NumberType()], v.AnyType()) ],

           [ "make_crp",typed_nr(crp.MakeCRPOutputPSP(), [v.NumberType()], v.AnyType()) ],

           [ "make_lazy_hmm",typed_nr(hmm.MakeUncollapsedHMMOutputPSP(), [v.SimplexType(), v.MatrixType(), v.MatrixType()], v.AnyType()) ],
  ]

def builtInSPs():
  return dict(builtInSPsList())
