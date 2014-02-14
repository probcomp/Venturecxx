#ifndef SPS_DSTRUCTURE_H
#define SPS_DSTRUCTURE_H

#include "psp.h"

struct SimplexOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};


#endif
