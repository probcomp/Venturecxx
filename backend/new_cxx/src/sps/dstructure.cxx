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

/* Polymorphic operators */

VentureValuePtr LookupOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[0]->lookup(args->operandValues[1]);
}

VentureValuePtr ContainsOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(args->operandValues[0]->contains(args->operandValues[1])));
}


VentureValuePtr SizeOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureNumber(args->operandValues[0]->size()));
}

/* Dicts */

VentureValuePtr DictOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{

}


/* Arrays */

VentureValuePtr ArrayOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{

}


VentureValuePtr IsArrayOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{

}


