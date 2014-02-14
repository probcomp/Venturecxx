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
  VentureValuePtrMap<VentureValuePtr> d;
  vector<VentureValuePtr> syms = args->operandValues[0]->getArray();
  vector<VentureValuePtr> vals = args->operandValues[1]->getArray();
  assert(syms.size() == vals.size());
  for (size_t i = 0; i < syms.size(); ++i) { d[syms[i]] = vals[i]; }
  return VentureValuePtr(new VentureDictionary(d));
}


/* Arrays */

VentureValuePtr ArrayOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureArray(args->operandValues));
}


VentureValuePtr IsArrayOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureArray>(args->operandValues[0])));
}


