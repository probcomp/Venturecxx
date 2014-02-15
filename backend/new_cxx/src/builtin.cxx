#include "builtin.h"
#include "sp.h"
#include "sps/conditional.h"
#include "sps/continuous.h"
#include "sps/csp.h"
#include "sps/deterministic.h"
#include "sps/dir_mult.h"
#include "sps/discrete.h"
#include "sps/dstructure.h"
#include "sps/eval.h"
#include "sps/msp.h"

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
  m["plus"] = new SP(new NullRequestPSP(), new PlusOutputPSP());
  m["minus"] = new SP(new NullRequestPSP(), new MinusOutputPSP());
  m["times"] = new SP(new NullRequestPSP(), new TimesOutputPSP());
  m["div"] = new SP(new NullRequestPSP(), new DivOutputPSP());
  m["eq"] = new SP(new NullRequestPSP(), new EqOutputPSP());
  m["gt"] = new SP(new NullRequestPSP(), new GtOutputPSP());
  m["gte"] = new SP(new NullRequestPSP(), new GteOutputPSP());
  m["lt"] = new SP(new NullRequestPSP(), new LtOutputPSP());
  m["lte"] = new SP(new NullRequestPSP(), new LteOutputPSP());
  m["sin"] = new SP(new NullRequestPSP(), new SinOutputPSP());
  m["cos"] = new SP(new NullRequestPSP(), new CosOutputPSP());
  m["tan"] = new SP(new NullRequestPSP(), new TanOutputPSP());
  m["hypot"] = new SP(new NullRequestPSP(), new HypotOutputPSP());
  m["exp"] = new SP(new NullRequestPSP(), new ExpOutputPSP());
  m["log"] = new SP(new NullRequestPSP(), new LogOutputPSP());
  m["pow"] = new SP(new NullRequestPSP(), new PowOutputPSP());
  m["sqrt"] = new SP(new NullRequestPSP(), new SqrtOutputPSP());
  m["not"] = new SP(new NullRequestPSP(), new NotOutputPSP());
  m["is_symbol"] = new SP(new NullRequestPSP(), new IsSymbolOutputPSP());
  
  /* Continuous SPs */
  m["normal"] = new SP(new NullRequestPSP(), new NormalPSP());
  m["gamma"] = new SP(new NullRequestPSP(), new GammaPSP());
  m["inv_gamma"] = new SP(new NullRequestPSP(), new InvGammaPSP());
  m["uniform_continuous"] = new SP(new NullRequestPSP(), new UniformContinuousPSP());
  m["beta"] = new SP(new NullRequestPSP(), new BetaPSP());
  m["student_t"] = new SP(new NullRequestPSP(), new StudentTPSP());
  m["chi_sq"] = new SP(new NullRequestPSP(), new ChiSquaredPSP());
  m["inv_chi_sq"] = new SP(new NullRequestPSP(), new InvChiSquaredPSP());

  /* Discrete SPs */
  m["bernoulli"] = new SP(new NullRequestPSP(), new BernoulliOutputPSP());
  m["flip"] = new SP(new NullRequestPSP(), new BernoulliOutputPSP());
  m["categorical"] = new SP(new NullRequestPSP(), new CategoricalOutputPSP());

  /* Conditiionals */
  m["branch"] = new SP(new BranchRequestPSP(), new ESRRefOutputPSP());
  m["biplex"] = new SP(new NullRequestPSP(), new BiplexOutputPSP());

  /* Eval and envs */
  m["eval"] = new SP(new EvalRequestPSP(), new ESRRefOutputPSP());
  m["get_current_environment"] = new SP(new NullRequestPSP(), new GetCurrentEnvOutputPSP());
  m["get_empty_environment"] = new SP(new NullRequestPSP(), new GetEmptyEnvOutputPSP());
  m["extend_environment"] = new SP(new NullRequestPSP(), new ExtendEnvOutputPSP());


  /* Data structures */
  m["simplex"] = new SP(new NullRequestPSP(), new SimplexOutputPSP());
  m["lookup"] = new SP(new NullRequestPSP(), new LookupOutputPSP());
  m["contains"] = new SP(new NullRequestPSP(), new ContainsOutputPSP());
  m["size"] = new SP(new NullRequestPSP(), new SizeOutputPSP());
  m["dict"] = new SP(new NullRequestPSP(), new DictOutputPSP());
  m["array"] = new SP(new NullRequestPSP(), new ArrayOutputPSP());
  m["prepend"] = new SP(new NullRequestPSP(), new PrependOutputPSP());
  m["is_array"] = new SP(new NullRequestPSP(), new IsArrayOutputPSP());
  m["pair"] = new SP(new NullRequestPSP(), new PairOutputPSP());
  m["is_pair"] = new SP(new NullRequestPSP(), new IsPairOutputPSP());
  m["list"] = new SP(new NullRequestPSP(), new ListOutputPSP());
  m["first"] = new SP(new NullRequestPSP(), new FirstOutputPSP());
  m["rest"] = new SP(new NullRequestPSP(), new RestOutputPSP());

  m["make_csp"] = new SP(new NullRequestPSP(), new MakeCSPOutputPSP());
  m["mem"] = new SP(new NullRequestPSP(), new MakeMSPOutputPSP());

  m["make_sym_dir_mult"] = new SP(new NullRequestPSP(), new MakeSymDirMultOutputPSP());
  m["make_uc_sym_dir_mult"] = new SP(new NullRequestPSP(), new MakeUCSymDirMultOutputPSP());
  
  return m;
}
