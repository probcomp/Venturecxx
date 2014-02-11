#include "builtin.h"
#include "sp.h"
#include "sps/deterministic.h"

map<string,VentureValuePtr> initBuiltInValues() 
{
  map<string,VentureValuePtr> m;
  m["true"] = shared_ptr<VentureBool>(true);
  m["false"] = shared_ptr<VentureBool>(false);
  return m;
}

map<string,shared_ptr<VentureSP> > initBuiltInSPs()
{
  map<string,shared_ptr<VentureSP> > m;

  /* Deterministic SPs */
  m["plus"] = SP(NullRequestPSP(),PlusOutputPSP());
  m["minus"] = SP(NullRequestPSP(),MinusOutputPSP());
  m["times"] = SP(NullRequestPSP(),TimesOutputPSP());
  m["div"] = SP(NullRequestPSP(),DivOutputPSP());
  m["eq"] = SP(NullRequestPSP(),EqOutputPSP());
  m["gt"] = SP(NullRequestPSP(),GtOutputPSP());
  m["gte"] = SP(NullRequestPSP(),GteOutputPSP());
  m["lt"] = SP(NullRequestPSP(),LtOutputPSP());
  m["lte"] = SP(NullRequestPSP(),LteOutputPSP());
  m["sin"] = SP(NullRequestPSP(),SinOutputPSP());
  m["cos"] = SP(NullRequestPSP(),CosOutputPSP());
  m["tan"] = SP(NullRequestPSP(),TanOutputPSP());
  m["hypot"] = SP(NullRequestPSP(),HypotOutputPSP());
  m["exp"] = SP(NullRequestPSP(),ExpOutputPSP());
  m["log"] = SP(NullRequestPSP(),LogOutputPSP());
  m["pow"] = SP(NullRequestPSP(),PowOutputPSP());
  m["sqrt"] = SP(NullRequestPSP(),SqrtOutputPSP());
  m["not"] = SP(NullRequestPSP(),NotOutputPSP());
  m["is_symbol"] = SP(NullRequestPSP(),IsSymbolOutputPSP());

  return m;
}
