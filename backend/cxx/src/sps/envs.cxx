#include "sps/envs.h"
#include "value.h"
#include "env.h"
#include "node.h"
#include "utils.h"

VentureValue * GetCurrentEnvSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  return node->familyEnv;
}

void GetCurrentEnvSP::flushOutput(VentureValue * value) const { }


VentureValue * GetEmptyEnvSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  return new VentureEnvironment;
}

VentureValue * ExtendEnvSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureEnvironment * env = dynamic_cast<VentureEnvironment*>(node->operandNodes[0]->getValue());
  
  VentureEnvironment * extendedEnv = new VentureEnvironment(env);
  VentureSymbol * vsym = dynamic_cast<VentureSymbol*>(node->operandNodes[1]->getValue());
  assert(vsym);
  extendedEnv->addBinding(vsym,node->operandNodes[2]);
  return extendedEnv;
}

