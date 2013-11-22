
#include "spaux.h"
#include "value.h"
#include "utils.h"
#include "env.h"
#include "sps/cond.h"


#include <cassert>
#include <string>
#include <vector>

#include <boost/functional/hash.hpp>


VentureValue * BranchSP::simulateRequest(const Args & args, gsl_rng * rng) const
{
  size_t id = reinterpret_cast<size_t>(args.outputNode);

  VentureEnvironment * extendedEnv = new VentureEnvironment(args.familyEnv);


  VentureBool * b = dynamic_cast<VentureBool *>(args.operands[0]);
  assert(b);

  size_t index = 2;
  if (b->pred) { index = 1; }
  extendedEnv->addBinding(new VentureSymbol("f"),args.operandNodes[index]);
  VenturePair * exp = new VenturePair(new VentureSymbol("f"),new VentureNil);
  return new VentureRequest({ESR(id,exp,extendedEnv)});
}

void BranchSP::flushRequest(VentureValue * value) const
{
  VentureRequest * requests = dynamic_cast<VentureRequest*>(value);
  assert(requests);
  assert(requests->esrs.size() == 1);
  ESR esr = requests->esrs[0];
  VenturePair * exp = dynamic_cast<VenturePair*>(esr.exp);
  delete exp->first;
  listShallowDestroy(exp);
  esr.env->destroySymbols();
  delete esr.env;
  delete value;
}

////////////

VentureValue * BiplexSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  assert(args.operands[0]);
  VentureBool * b = dynamic_cast<VentureBool *>(args.operands[0]);
  bool pred;
  if (b) { pred = b->pred; }
  else
  {
    VentureNumber * n = dynamic_cast<VentureNumber *>(args.operands[0]);
    assert(n);
    pred = (n->x != 0);
  }
  if (pred) { return args.operands[1]; }
  else { return args.operands[2]; }
}

void BiplexSP::flushOutput(VentureValue * value) const {}
