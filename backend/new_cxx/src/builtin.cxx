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

map<string,shared_ptr<VentureSP> > initBuiltInSPs()
{
  map<string,shared_ptr<VentureSP> > m;

  /* Deterministic SPs */
  m["plus"] = new VentureSP(new NullRequestPSP(), new PlusOutputPSP());
  m["minus"] = new VentureSP(new NullRequestPSP(), new MinusOutputPSP());
  m["times"] = new VentureSP(new NullRequestPSP(), new TimesOutputPSP());
  m["div"] = new VentureSP(new NullRequestPSP(), new DivOutputPSP());
  m["eq"] = new VentureSP(new NullRequestPSP(), new EqOutputPSP());
  m["gt"] = new VentureSP(new NullRequestPSP(), new GtOutputPSP());
  m["gte"] = new VentureSP(new NullRequestPSP(), new GteOutputPSP());
  m["lt"] = new VentureSP(new NullRequestPSP(), new LtOutputPSP());
  m["lte"] = new VentureSP(new NullRequestPSP(), new LteOutputPSP());
  m["sin"] = new VentureSP(new NullRequestPSP(), new SinOutputPSP());
  m["cos"] = new VentureSP(new NullRequestPSP(), new CosOutputPSP());
  m["tan"] = new VentureSP(new NullRequestPSP(), new TanOutputPSP());
  m["hypot"] = new VentureSP(new NullRequestPSP(), new HypotOutputPSP());
  m["exp"] = new VentureSP(new NullRequestPSP(), new ExpOutputPSP());
  m["log"] = new VentureSP(new NullRequestPSP(), new LogOutputPSP());
  m["pow"] = new VentureSP(new NullRequestPSP(), new PowOutputPSP());
  m["sqrt"] = new VentureSP(new NullRequestPSP(), new SqrtOutputPSP());
  m["not"] = new VentureSP(new NullRequestPSP(), new NotOutputPSP());
  m["is_symbol"] = new VentureSP(new NullRequestPSP(), new IsSymbolOutputPSP());
  
  /* Continuous SPs */
  m["normal"] = new VentureSP(new NullRequestPSP(), new NormalPSP());
  m["gamma"] = new VentureSP(new NullRequestPSP(), new GammaPSP());
  m["inv_gamma"] = new VentureSP(new NullRequestPSP(), new InvGammaPSP());
  m["uniform_continuous"] = new VentureSP(new NullRequestPSP(), new UniformContinuousPSP());
  m["beta"] = new VentureSP(new NullRequestPSP(), new BetaPSP());
  m["student_t"] = new VentureSP(new NullRequestPSP(), new StudentTPSP());
  m["chi_sq"] = new VentureSP(new NullRequestPSP(), new ChiSquaredPSP());
  m["inv_chi_sq"] = new VentureSP(new NullRequestPSP(), new InvChiSquaredPSP());

  /* Discrete SPs */
  m["bernoulli"] = new VentureSP(new NullRequestPSP(), new BernoulliOutputPSP());
  m["flip"] = new VentureSP(new NullRequestPSP(), new BernoulliOutputPSP());
  m["categorical"] = new VentureSP(new NullRequestPSP(), new CategoricalOutputPSP());

  /* Conditiionals */
  m["branch"] = new VentureSP(new BranchRequestPSP(), new ESRRefOutputPSP());
  m["biplex"] = new VentureSP(new NullRequestPSP(), new BiplexOutputPSP());

  /* Eval and envs */
  m["eval"] = new VentureSP(new EvalRequestPSP(), new ESRRefOutputPSP());
  m["get_current_environment"] = new VentureSP(new NullRequestPSP(), new GetCurrentEnvOutputPSP());
  m["get_empty_environment"] = new VentureSP(new NullRequestPSP(), new GetEmptyEnvOutputPSP());
  m["extend_environment"] = new VentureSP(new NullRequestPSP(), new ExtendEnvOutputPSP());


  /* Data structures */
  m["simplex"] = new VentureSP(new NullRequestPSP(), new SimplexOutputPSP());
  m["lookup"] = new VentureSP(new NullRequestPSP(), new LookupOutputPSP());
  m["contains"] = new VentureSP(new NullRequestPSP(), new ContainsOutputPSP());
  m["size"] = new VentureSP(new NullRequestPSP(), new SizeOutputPSP());
  m["dict"] = new VentureSP(new NullRequestPSP(), new DictOutputPSP());
  m["array"] = new VentureSP(new NullRequestPSP(), new ArrayOutputPSP());
  m["prepend"] = new VentureSP(new NullRequestPSP(), new PrependOutputPSP());
  m["is_array"] = new VentureSP(new NullRequestPSP(), new IsArrayOutputPSP());
  m["pair"] = new VentureSP(new NullRequestPSP(), new PairOutputPSP());
  m["is_pair"] = new VentureSP(new NullRequestPSP(), new IsPairOutputPSP());
  m["list"] = new VentureSP(new NullRequestPSP(), new ListOutputPSP());
  m["first"] = new VentureSP(new NullRequestPSP(), new FirstOutputPSP());
  m["rest"] = new VentureSP(new NullRequestPSP(), new RestOutputPSP());

  m["make_csp"] = new VentureSP(new NullRequestPSP(), new MakeCSPOutputPSP());
  m["mem"] = new VentureSP(new NullRequestPSP(), new MakeMSPOutputPSP());

  m["make_sym_dir_mult"] = new VentureSP(new NullRequestPSP(), new MakeSymDirMultOutputPSP());
  
  return m;
}
