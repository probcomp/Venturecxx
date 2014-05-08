#ifndef SPS_SCOPE_H
#define SPS_SCOPE_H

#include "psp.h"

struct ScopeIncludeOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  vector<VentureValuePtr> gradientOfSimulate(const shared_ptr<Args> args, const VentureValuePtr value, const VentureValuePtr direction) const;
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const;
};
  

#endif
