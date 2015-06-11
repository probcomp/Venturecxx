// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "builtin.h"
#include "sp.h"
#include "sps/conditional.h"
#include "sps/continuous.h"
#include "sps/crp.h"
#include "sps/csp.h"
#include "sps/deterministic.h"
#include "sps/dir_mult.h"
#include "sps/betabernoulli.h"
#include "sps/discrete.h"
#include "sps/dstructure.h"
#include "sps/eval.h"
#include "sps/hmm.h"
#include "sps/matrix.h"
#include "sps/misc.h"
#include "sps/msp.h"
#include "sps/mvn.h"
#include "sps/scope.h"

map<string,VentureValuePtr> initBuiltInValues()
{
  map<string,VentureValuePtr> m;
  m["true"] = shared_ptr<VentureBool>(new VentureBool(true));
  m["false"] = shared_ptr<VentureBool>(new VentureBool(false));
  m["nil"] = shared_ptr<VentureNil>(new VentureNil());
  return m;
}

map<string,SP*> initBuiltInSPs()
{
  map<string,SP*> m;

  /* Deterministic SPs */
  m["add"] = new SP(new NullRequestPSP(), new AddOutputPSP());
  m["sub"] = new SP(new NullRequestPSP(), new SubOutputPSP());
  m["mul"] = new SP(new NullRequestPSP(), new MulOutputPSP());
  m["div"] = new SP(new NullRequestPSP(), new DivOutputPSP());
  m["int_div"] = new SP(new NullRequestPSP(), new IntDivOutputPSP());
  m["int_mod"] = new SP(new NullRequestPSP(), new IntModOutputPSP());
  m["eq"] = new SP(new NullRequestPSP(), new EqOutputPSP());
  m["gt"] = new SP(new NullRequestPSP(), new GtOutputPSP());
  m["gte"] = new SP(new NullRequestPSP(), new GteOutputPSP());
  m["lt"] = new SP(new NullRequestPSP(), new LtOutputPSP());
  m["lte"] = new SP(new NullRequestPSP(), new LteOutputPSP());
  m["floor"] = new SP(new NullRequestPSP(), new FloorOutputPSP());
  m["sin"] = new SP(new NullRequestPSP(), new SinOutputPSP());
  m["cos"] = new SP(new NullRequestPSP(), new CosOutputPSP());
  m["tan"] = new SP(new NullRequestPSP(), new TanOutputPSP());
  m["hypot"] = new SP(new NullRequestPSP(), new HypotOutputPSP());
  m["exp"] = new SP(new NullRequestPSP(), new ExpOutputPSP());
  m["log"] = new SP(new NullRequestPSP(), new LogOutputPSP());
  m["pow"] = new SP(new NullRequestPSP(), new PowOutputPSP());
  m["sqrt"] = new SP(new NullRequestPSP(), new SqrtOutputPSP());
  m["not"] = new SP(new NullRequestPSP(), new NotOutputPSP());
  m["is_number"] = new SP(new NullRequestPSP(), new IsNumberOutputPSP());
  m["is_integer"] = new SP(new NullRequestPSP(), new IsIntegerOutputPSP());
  m["is_boolean"] = new SP(new NullRequestPSP(), new IsBoolOutputPSP());
  m["is_symbol"] = new SP(new NullRequestPSP(), new IsSymbolOutputPSP());

  m["to_atom"] = new SP(new NullRequestPSP(), new ToAtomOutputPSP());
  m["is_atom"] = new SP(new NullRequestPSP(), new IsAtomOutputPSP());

  m["probability"] = new SP(new NullRequestPSP(), new ProbabilityOutputPSP());
  m["is_probability"] = new SP(new NullRequestPSP(), new IsProbabilityOutputPSP());

  /* Continuous SPs */
  m["normal"] = new SP(new NullRequestPSP(), new NormalPSP());
  m["gamma"] = new SP(new NullRequestPSP(), new GammaPSP());
  m["inv_gamma"] = new SP(new NullRequestPSP(), new InvGammaPSP());
  m["expon"] = new SP(new NullRequestPSP(), new ExponentialPSP());
  m["uniform_continuous"] = new SP(new NullRequestPSP(), new UniformContinuousPSP());
  m["beta"] = new SP(new NullRequestPSP(), new BetaPSP());
  m["student_t"] = new SP(new NullRequestPSP(), new StudentTPSP());
  m["chi_sq"] = new SP(new NullRequestPSP(), new ChiSquaredPSP());
  m["inv_chi_sq"] = new SP(new NullRequestPSP(), new InvChiSquaredPSP());
  m["approx_binomial"] = new SP(new NullRequestPSP(), new ApproximateBinomialPSP());

  m["multivariate_normal"] = new SP(new NullRequestPSP(), new MVNormalPSP());

  /* Discrete SPs */
  m["bernoulli"] = new SP(new NullRequestPSP(), new BernoulliOutputPSP());
  m["flip"] = new SP(new NullRequestPSP(), new FlipOutputPSP());
  m["uniform_discrete"] = new SP(new NullRequestPSP(), new UniformDiscreteOutputPSP());
  m["binomial"] = new SP(new NullRequestPSP(), new BinomialOutputPSP());
  m["categorical"] = new SP(new NullRequestPSP(), new CategoricalOutputPSP());
  m["log_categorical"] = new SP(new NullRequestPSP(), new LogCategoricalOutputPSP());
  m["symmetric_dirichlet"] = new SP(new NullRequestPSP(), new SymmetricDirichletOutputPSP());
  m["dirichlet"] = new SP(new NullRequestPSP(), new DirichletOutputPSP());
  m["poisson"] = new SP(new NullRequestPSP(), new PoissonOutputPSP());

  /* Conditionals */
  m["branch"] = new SP(new BranchRequestPSP(), new ESRRefOutputPSP());
  m["biplex"] = new SP(new NullRequestPSP(), new BiplexOutputPSP());

  /* Eval and envs */
  m["eval"] = new SP(new EvalRequestPSP(), new ESRRefOutputPSP());
  m["get_current_environment"] = new SP(new NullRequestPSP(), new GetCurrentEnvOutputPSP());
  m["get_empty_environment"] = new SP(new NullRequestPSP(), new GetEmptyEnvOutputPSP());
  m["extend_environment"] = new SP(new NullRequestPSP(), new ExtendEnvOutputPSP());
  m["is_environment"] = new SP(new NullRequestPSP(), new IsEnvOutputPSP());

  /* Latents */
  m["make_lazy_hmm"] = new SP(new NullRequestPSP(), new MakeUncollapsedHMMOutputPSP());

  /* Matrices */
  m["matrix"] = new SP(new NullRequestPSP(), new MatrixOutputPSP());
  m["is_matrix"] = new SP(new NullRequestPSP(), new IsMatrixOutputPSP());
  m["id_matrix"] = new SP(new NullRequestPSP(), new IdentityMatrixOutputPSP());
  m["vector"] = new SP(new NullRequestPSP(), new VectorOutputPSP());
  m["is_vector"] = new SP(new NullRequestPSP(), new IsVectorOutputPSP());
  m["to_vector"] = new SP(new NullRequestPSP(), new ToVectorOutputPSP());
  m["vector_dot"] = new SP(new NullRequestPSP(), new VectorDotOutputPSP());
  m["matrix_times_vector"] = new SP(new NullRequestPSP(), new MatrixTimesVectorOutputPSP());

  /* Scoping */
  m["tag"] = new SP(new NullRequestPSP(), new TagOutputPSP());
  m["tag_exclude"] = new SP(new NullRequestPSP(), new TagExcludeOutputPSP());

  /* Data structures */
  m["simplex"] = new SP(new NullRequestPSP(), new SimplexOutputPSP());
  m["is_simplex"] = new SP(new NullRequestPSP(), new IsSimplexOutputPSP());
  m["to_simplex"] = new SP(new NullRequestPSP(), new ToSimplexOutputPSP());

  m["lookup"] = new SP(new NullRequestPSP(), new LookupOutputPSP());
  m["contains"] = new SP(new NullRequestPSP(), new ContainsOutputPSP());
  m["size"] = new SP(new NullRequestPSP(), new SizeOutputPSP());
  m["dict"] = new SP(new NullRequestPSP(), new DictOutputPSP());
  m["is_dict"] = new SP(new NullRequestPSP(), new IsDictOutputPSP());
  m["array"] = new SP(new NullRequestPSP(), new ArrayOutputPSP());
  m["prepend"] = new SP(new NullRequestPSP(), new PrependOutputPSP());
  m["append"] = new SP(new NullRequestPSP(), new AppendOutputPSP());
  m["concat"] = new SP(new NullRequestPSP(), new ConcatOutputPSP());
  m["is_array"] = new SP(new NullRequestPSP(), new IsArrayOutputPSP());
  m["to_array"] = new SP(new NullRequestPSP(), new ToArrayOutputPSP());
  m["pair"] = new SP(new NullRequestPSP(), new PairOutputPSP());
  m["is_pair"] = new SP(new NullRequestPSP(), new IsPairOutputPSP());
  m["list"] = new SP(new NullRequestPSP(), new ListOutputPSP());
  m["first"] = new SP(new NullRequestPSP(), new FirstOutputPSP());
  m["second"] = new SP(new NullRequestPSP(), new SecondOutputPSP());
  m["rest"] = new SP(new NullRequestPSP(), new RestOutputPSP());
  m["apply"] = new SP(new ApplyRequestPSP(), new ESRRefOutputPSP());
  m["mapv"] = new SP(new ArrayMapRequestPSP(), new ESRArrayOutputPSP());
  m["imapv"] = new SP(new IndexedArrayMapRequestPSP(), new ESRArrayOutputPSP());
  m["arange"] = new SP(new NullRequestPSP(), new ArangeOutputPSP());
  m["repeat"] = new SP(new NullRequestPSP(), new RepeatOutputPSP());

  m["make_csp"] = new SP(new NullRequestPSP(), new MakeCSPOutputPSP());
  m["mem"] = new SP(new NullRequestPSP(), new MakeMSPOutputPSP());

  /* Beta bernoullis */
  m["make_beta_bernoulli"] = new SP(new NullRequestPSP(), new MakeBetaBernoulliOutputPSP());
  m["make_uc_beta_bernoulli"] = new SP(new NullRequestPSP(), new MakeUBetaBernoulliOutputPSP());

  /* Dir mults */
  m["make_sym_dir_mult"] = new SP(new NullRequestPSP(), new MakeSymDirMultOutputPSP());
  m["make_dir_mult"] = new SP(new NullRequestPSP(), new MakeDirMultOutputPSP());
  m["make_uc_sym_dir_mult"] = new SP(new NullRequestPSP(), new MakeUCSymDirMultOutputPSP());
  m["make_uc_dir_mult"] = new SP(new NullRequestPSP(), new MakeUCDirMultOutputPSP());

  /* Non parametrics */
  m["make_crp"] = new SP(new NullRequestPSP(), new MakeCRPOutputPSP());
  
  /* Misc */
  m["exactly"] = new SP(new NullRequestPSP(), new ExactlyOutputPSP());
  
  return m;
}
