#include "sps/conditional.h"
#include "utils.h"

VentureValuePtr BranchRequestPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("branch", args, 3);
  
  int expIndex = 2;
  if (args->operandValues[0]->getBool()) { expIndex = 1; }
  VentureValuePtr expression = args->operandValues[expIndex];

  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureID()),expression,args->env));
  return shared_ptr<VentureRequest>(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}

VentureValuePtr BiplexOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("if", args, 3);
  if (args->operandValues[0]->getBool()) { return args->operandValues[1]; }
  else { return args->operandValues[2]; }
}

