#ifndef SPS_CONDITIONAL_H
#define SPS_CONDITIONAL_H

#include "psp.h"

struct BranchRequestPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct BiplexOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};


#endif
