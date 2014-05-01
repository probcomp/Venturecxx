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

VentureValuePtr IsSimplexOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureSimplex>(args->operandValues[0]) != NULL));
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

VentureValuePtr IsDictOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureDictionary>(args->operandValues[0]) != NULL));
}



/* Arrays */

VentureValuePtr ArrayOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureArray(args->operandValues));
}

VentureValuePtr PrependOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  vector<VentureValuePtr> v;
  v.push_back(args->operandValues[0]);
  vector<VentureValuePtr> old = args->operandValues[1]->getArray();
  v.insert(v.end(), old.begin(), old.end());
  return VentureValuePtr(new VentureArray(v));
}



VentureValuePtr IsArrayOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureArray>(args->operandValues[0]) != NULL));
}


/* Lists */

VentureValuePtr PairOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VenturePair(args->operandValues[0],args->operandValues[1]));
}

VentureValuePtr IsPairOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VenturePair>(args->operandValues[0]) != NULL));
}


VentureValuePtr ListOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  VentureValuePtr l(new VentureNil());
  for (size_t i = args->operandValues.size(); i > 0; --i)
  {
    l = VentureValuePtr(new VenturePair(args->operandValues[i-1],l));
  }
  return l;
}

VentureValuePtr FirstOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[0]->getFirst();
}

VentureValuePtr SecondOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[0]->getRest()->getFirst();
}


VentureValuePtr RestOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[0]->getRest();
}
