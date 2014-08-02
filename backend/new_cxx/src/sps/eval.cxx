#include "sps/eval.h"
#include "env.h"
#include "values.h"

VentureValuePtr EvalRequestPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  shared_ptr<VentureEnvironment> env = dynamic_pointer_cast<VentureEnvironment>(args->operandValues[1]);
  assert(env);
  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureID()),args->operandValues[0],env));
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}

VentureValuePtr GetCurrentEnvOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->env;
}

VentureValuePtr GetEmptyEnvOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureEnvironment());
}

VentureValuePtr ExtendEnvOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  shared_ptr<VentureEnvironment> env = dynamic_pointer_cast<VentureEnvironment>(args->operandValues[0]);
  assert(env);

  vector<shared_ptr<VentureSymbol> > syms;
  vector<Node*> nodes;

  shared_ptr<VentureSymbol> sym = dynamic_pointer_cast<VentureSymbol>(args->operandValues[1]);
  assert(sym);
  syms.push_back(sym);
  nodes.push_back(args->operandNodes[2]);
  return VentureValuePtr(new VentureEnvironment(env,syms,nodes));
}

VentureValuePtr IsEnvOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureEnvironment>(args->operandValues[0]) != NULL));
}
