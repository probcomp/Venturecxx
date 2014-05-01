#ifndef MVN_SP_H
#define MVN_SP_H

#include "psp.h"

struct MVNormalPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

#endif
