#include "sps/discrete.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>

VentureValuePtr BernoulliOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }
  int n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  return shared_ptr<VentureBool>(new VentureBool(n));
}

double BernoulliOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }

  if (value->getBool()) { return log(p); }
  else { return log(1 - p); }
}
