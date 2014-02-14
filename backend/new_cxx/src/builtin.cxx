#include "builtin.h"
#include "sp.h"
#include "sps/deterministic.h"
#include "sps/csp.h"
#include "sps/continuous.h"

map<string,VentureValuePtr> initBuiltInValues() 
{
  map<string,VentureValuePtr> m;
  m["true"] = shared_ptr<VentureBool>(new VentureBool(true));
  m["false"] = shared_ptr<VentureBool>(new VentureBool(false));
  return m;
}

map<string,shared_ptr<VentureSP> > initBuiltInSPs()
{
  map<string,shared_ptr<VentureSP> > m;

  /* Deterministic SPs */
  m["plus"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new PlusOutputPSP()));
  m["minus"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new MinusOutputPSP()));
  m["times"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new TimesOutputPSP()));
  m["div"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new DivOutputPSP()));
  m["eq"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new EqOutputPSP()));
  m["gt"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new GtOutputPSP()));
  m["gte"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new GteOutputPSP()));
  m["lt"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new LtOutputPSP()));
  m["lte"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new LteOutputPSP()));
  m["sin"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new SinOutputPSP()));
  m["cos"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new CosOutputPSP()));
  m["tan"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new TanOutputPSP()));
  m["hypot"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new HypotOutputPSP()));
  m["exp"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new ExpOutputPSP()));
  m["log"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new LogOutputPSP()));
  m["pow"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new PowOutputPSP()));
  m["sqrt"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new SqrtOutputPSP()));
  m["not"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new NotOutputPSP()));
  m["is_symbol"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new IsSymbolOutputPSP()));
  
  /* Continuous SPs */
  m["normal"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new NormalPSP()));
  m["gamma"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new GammaPSP()));
  m["inv_gamma"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new InvGammaPSP()));
  m["uniform_continuous"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new UniformContinuousPSP()));
  m["beta"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new BetaPSP()));
  m["student_t"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new StudentTPSP()));
  m["chi_sq"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new ChiSquaredPSP()));
  m["inv_chi_sq"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new InvChiSquaredPSP()));

  m["make_csp"] = shared_ptr<VentureSP>(new VentureSP(new NullRequestPSP(), new MakeCSPOutputPSP()));
  
  
  
  return m;
}
