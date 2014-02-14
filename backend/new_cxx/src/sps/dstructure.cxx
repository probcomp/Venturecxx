#include "sps/dstructure.h"
#include "values.h"

VentureValuePtr SimplexOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  Simplex s;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    s.push_back(args->operandValues[i]->getDouble());
  }
  return VentureValuePtr(new VentureSimplex(s));
}
