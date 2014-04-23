import math
import numpy as np

from sp import VentureSP, SPType
from psp import NullRequestPSP, ESRRefOutputPSP, DeterministicPSP, TypedPSP

import discrete
import dirichlet
import continuous
import dstructures
import csp
import crp
import cmvn
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
  return { "true" : v.VentureBool(True), "false" : v.VentureBool(False), "nil" : v.VentureNil() }

def no_request(output): return VentureSP(NullRequestPSP(), output)

def esr_output(request): return VentureSP(request, ESRRefOutputPSP())

def typed_nr(output, args_types, return_type, **kwargs):
  return no_request(TypedPSP(output, SPType(args_types, return_type, **kwargs)))

def func_psp(f, descr=None, sim_grad=None):
  class FunctionPSP(DeterministicPSP):
    def __init__(self, descr):
      self.descr = descr
      self.sim_grad = sim_grad
      if self.descr is None:
        self.descr = "deterministic %s"
    def simulate(self,args):
      return f(args)
    def gradientOfSimulate(self, args, _value, direction):
      # Don't need the value if the function is deterministic, because
      # it consumes no randomness.
      if self.sim_grad:
        return self.sim_grad(args, direction)
      else:
        raise Exception("Cannot compute simulation gradient of %s", self.descr)
    def description(self,name):
      return self.descr % name
  return FunctionPSP(descr)

def typed_func_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(func_psp(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def typed_func(*args, **kwargs):
  return no_request(typed_func_psp(*args, **kwargs))

# TODO This should actually be named to distinguish it from the
# previous version, which accepts the whole args object (where this
# one splats the operand values).
def deterministic_psp(f, descr=None, sim_grad=None):
  def new_grad(args, direction):
    return sim_grad(args.operandValues, direction)
  return func_psp(lambda args: f(*args.operandValues), descr, sim_grad=(new_grad if sim_grad else None))

def deterministic_typed_psp(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return TypedPSP(deterministic_psp(f, descr, sim_grad), SPType(args_types, return_type, **kwargs))

def deterministic(f, descr=None, sim_grad=None):
  return no_request(deterministic_psp(f, descr, sim_grad))

def deterministic_typed(f, args_types, return_type, descr=None, sim_grad=None, **kwargs):
  return typed_nr(deterministic_psp(f, descr, sim_grad), args_types, return_type, **kwargs)

def binaryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType(), v.NumberType()], v.NumberType(), descr=descr)

def binaryNumS(output):
  return typed_nr(output, [v.NumberType(), v.NumberType()], v.NumberType())

def unaryNum(f, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), descr=descr)

def unaryNumS(f):
  return typed_nr(f, [v.NumberType()], v.NumberType())

def naryNum(f, sim_grad=None, descr=None):
  return deterministic_typed(f, [v.NumberType()], v.NumberType(), variadic=True, sim_grad=sim_grad, descr=descr)

def zero_gradient(args, _direction):
  return [0 for _ in args]

def binaryPred(f, descr=None):
  return deterministic_typed(f, [v.AnyType(), v.AnyType()], v.BoolType(), sim_grad=zero_gradient, descr=descr)

def type_test(t):
  return deterministic_typed(lambda thing: thing in t, [v.AnyType()], v.BoolType(),
                             sim_grad = zero_gradient,
                             descr="%s returns true iff its argument is a " + t.name())

def grad_times(args, direction):
  assert len(args) == 2, "Gradient only available for binary multiply"
  return [direction*args[1], direction*args[0]]

def builtInSPsList():
  return [ [ "add",  naryNum(lambda *args: sum(args),
                              sim_grad=lambda args, direction: [direction for _ in args],
                              descr="%s returns the sum of all its arguments") ],
           [ "sub", binaryNum(lambda x,y: x - y,
                                "%s returns the difference between its first and second arguments") ],
           [ "mul", naryNum(lambda *args: reduce(lambda x,y: x * y,args,1),
                              sim_grad=grad_times,
                              descr="%s returns the product of all its arguments") ],           
           [ "div",   binaryNum(lambda x,y: x / y,
                                "%s returns the quotient of its first argument by its second") ],
           [ "eq",    binaryPred(lambda x,y: x.compare(y) == 0,
                                 descr="%s compares its two arguments for equality") ],
           [ "gt",    binaryPred(lambda x,y: x.compare(y) >  0,
                                 descr="%s returns true if its first argument compares greater than its second") ],
           [ "gte",   binaryPred(lambda x,y: x.compare(y) >= 0,
                                 descr="%s returns true if its first argument compares greater than or equal to its second") ],
           [ "lt",    binaryPred(lambda x,y: x.compare(y) <  0,
                                 descr="%s returns true if its first argument compares less than its second") ],
           [ "lte",   binaryPred(lambda x,y: x.compare(y) <= 0,
                                 descr="%s returns true if its first argument compares less than or equal to its second") ],
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

           [ "list", deterministic_typed(lambda *args: args, [v.AnyType()], v.ListType(), variadic=True,
                                         descr="%s returns the list of its arguments") ],
           [ "pair", deterministic_typed(lambda a,d: (a,d), [v.AnyType(), v.AnyType()], v.PairType(),
                                         descr="%s returns the pair whose first component is the first argument and whose second component is the second argument") ],
           [ "is_pair", type_test(v.PairType()) ],
           [ "first", deterministic_typed(lambda p: p[0], [v.PairType()], v.AnyType(),
                                          "%s returns the first component of its argument pair") ],
           [ "rest", deterministic_typed(lambda p: p[1], [v.PairType()], v.AnyType(),
                                         "%s returns the second component of its argument pair") ],
           [ "second", deterministic_typed(lambda p: p[1].first, [v.PairType()], v.AnyType(),
                                           "%s returns the first component of the second component of its argument") ],


           [ "array", deterministic(lambda *args: v.VentureArray(np.array(args)),
                                    sim_grad=lambda args, direction: direction.getArray(),
                                    descr="%s :: <SP <object> ... -> <array>>\nReturns an array initialized with its arguments") ],
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
                                     sim_grad=lambda args, direction: [args[0].lookup_grad(args[1], direction), 0],
                                     descr="%s :: <SP <mapping k v> k -> v>\nLooks the given key up in the given mapping and returns the result.  It is an error if the key is not in the mapping.  Lists and arrays are viewed as mappings from indices to the corresponding elements.") ],
           [ "contains", deterministic(lambda xs, x: v.VentureBool(xs.contains(x)),
                                       "%s :: <SP <mapping k v> k -> <bool>>\nReports whether the given key appears in the given mapping or not.") ],
           [ "size", deterministic(lambda xs: v.VentureNumber(xs.size()),
                                   "%s :: <SP <collection> -> <number>>\nReturns the number of elements in the given collection") ],

           [ "branch", esr_output(conditionals.branch_request_psp()) ],
           [ "biplex", deterministic_typed(lambda p, c, a: c if p else a, [v.BoolType(), v.AnyType(), v.AnyType()], v.AnyType(),
                                           sim_grad=lambda args, direc: [0, direc, 0] if args[0] else [0, 0, direc],
                                           descr="%s returns either its second or third argument.")],
           [ "make_csp", no_request(csp.MakeCSPOutputPSP()) ],

           [ "get_current_environment", typed_func(lambda args: args.env, [], env.EnvironmentType(),
                                                   descr="%s returns the lexical environment of its invocation site") ],
           [ "get_empty_environment", typed_func(lambda args: env.VentureEnvironment(), [], env.EnvironmentType(),
                                                 descr="%s returns the empty environment") ],
           [ "is_environment", type_test(env.EnvironmentType()) ],
           [ "extend_environment",no_request(eval_sps.ExtendEnvOutputPSP()) ],
           [ "eval",VentureSP(eval_sps.EvalRequestPSP(),ESRRefOutputPSP()) ],

           [ "mem",no_request(msp.MakeMSPOutputPSP()) ],

           [ "scope_include",no_request(scope.ScopeIncludeOutputPSP()) ],

           [ "binomial", binaryNumS(discrete.BinomialOutputPSP()) ],
           [ "flip", typed_nr(discrete.FlipOutputPSP(), [v.NumberType()], v.BoolType(), min_req_args=0) ],
           [ "bernoulli", typed_nr(discrete.BernoulliOutputPSP(), [v.NumberType()], v.NumberType(), min_req_args=0) ],
           [ "categorical", typed_nr(discrete.CategoricalOutputPSP(), [v.SimplexType(), v.ArrayType()], v.AnyType(), min_req_args=1) ],

           [ "uniform_discrete",binaryNumS(discrete.UniformDiscreteOutputPSP()) ],
           [ "poisson",unaryNumS(discrete.PoissonOutputPSP()) ],
                      
           [ "normal",binaryNumS(continuous.NormalOutputPSP()) ],
           [ "uniform_continuous",binaryNumS(continuous.UniformOutputPSP()) ],
           [ "beta",binaryNumS(continuous.BetaOutputPSP()) ],
           [ "gamma",binaryNumS(continuous.GammaOutputPSP()) ],
           [ "student_t",typed_nr(continuous.StudentTOutputPSP(),[v.NumberType(),v.NumberType(),v.NumberType()], v.NumberType(), min_req_args=1 ) ],
           [ "inv_gamma",binaryNumS(continuous.InvGammaOutputPSP()) ],

           [ "multivariate_normal", typed_nr(continuous.MVNormalOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.MatrixType()], v.HomogeneousArrayType(v.NumberType())) ],
           [ "inv_wishart", typed_nr(continuous.InverseWishartPSP(), [v.MatrixType(), v.NumberType()], v.MatrixType())],
           [ "wishart", typed_nr(continuous.WishartPSP(), [v.MatrixType(), v.NumberType()], v.MatrixType())],
           
           [ "make_beta_bernoulli",typed_nr(discrete.MakerCBetaBernoulliOutputPSP(), [v.NumberType(), v.NumberType()], SPType([], v.BoolType())) ],
           [ "make_uc_beta_bernoulli",typed_nr(discrete.MakerUBetaBernoulliOutputPSP(), [v.NumberType(), v.NumberType()], SPType([], v.BoolType())) ],

           [ "dirichlet",typed_nr(dirichlet.DirichletOutputPSP(), [v.HomogeneousArrayType(v.NumberType())], v.SimplexType()) ],
           [ "symmetric_dirichlet",typed_nr(dirichlet.SymmetricDirichletOutputPSP(), [v.NumberType(), v.NumberType()], v.SimplexType()) ],

           [ "make_dir_mult",typed_nr(dirichlet.MakerCDirMultOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.ArrayType()], SPType([], v.AnyType()), min_req_args=1) ],
           [ "make_uc_dir_mult",typed_nr(dirichlet.MakerUDirMultOutputPSP(), [v.HomogeneousArrayType(v.NumberType()), v.ArrayType()], SPType([], v.AnyType()), min_req_args=1) ],

           [ "make_sym_dir_mult",typed_nr(dirichlet.MakerCSymDirMultOutputPSP(), [v.NumberType(), v.NumberType(), v.ArrayType()], SPType([], v.AnyType()), min_req_args=2) ], # Saying AnyType here requires the underlying psp to emit a VentureValue.
           [ "make_uc_sym_dir_mult",typed_nr(dirichlet.MakerUSymDirMultOutputPSP(), [v.NumberType(), v.NumberType(), v.ArrayType()], SPType([], v.AnyType()), min_req_args=2) ],

           [ "make_crp",typed_nr(crp.MakeCRPOutputPSP(), [v.NumberType(),v.NumberType()], SPType([], v.AtomType()), min_req_args = 1) ],
           [ "make_cmvn",typed_nr(cmvn.MakeCMVNOutputPSP(), [v.HomogeneousArrayType(v.NumberType()),v.NumberType(),v.NumberType(),v.MatrixType()], SPType([], SPType([], v.MatrixType()))) ],           

           [ "make_lazy_hmm",typed_nr(hmm.MakeUncollapsedHMMOutputPSP(), [v.SimplexType(), v.MatrixType(), v.MatrixType()], SPType([v.NumberType()], v.NumberType())) ],
  ]

def builtInSPs():
  return dict(builtInSPsList())
