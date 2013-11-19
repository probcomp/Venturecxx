#include "sps/envs.h"
#include "value.h"
#include "env.h"

#include "utils.h"

VentureValue * GetCurrentEnvSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  return args.familyEnv;
}

void GetCurrentEnvSP::flushOutput(VentureValue * value) const { }


VentureValue * GetEmptyEnvSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  return new VentureEnvironment;
}

VentureValue * ExtendEnvSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureEnvironment * env = dynamic_cast<VentureEnvironment*>(args.operands[0]);
  
  VentureEnvironment * extendedEnv = new VentureEnvironment(env);
  VentureSymbol * vsym = dynamic_cast<VentureSymbol*>(args.operands[1]);
  assert(vsym);
  extendedEnv->addBinding(vsym,args.operandNodes[2]);
  return extendedEnv;
}

