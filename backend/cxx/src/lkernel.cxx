#include "value.h"
#include "lkernel.h"
#include "node.h"
#include "sp.h"

VentureValue * DefaultAAAKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB,gsl_rng * rng) 
{
  return makerSP->simulateOutput(appNode,rng);
}

double DefaultAAAKernel::weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB)
{
  VentureSP * vsp = dynamic_cast<VentureSP *>(newVal);
  assert(vsp);

  double weight = vsp->sp->logDensityOfCounts(appNode->madeSPAux);
  LPRINT("DefaultAAAKernel::weight(): ", weight);
  return weight;
}

VentureValue * DeterministicLKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB,gsl_rng * rng)
{
  return value;
}

double DeterministicLKernel::weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB)
{
  assert(newVal == value);
  return sp->logDensity(value,appNode);
}

