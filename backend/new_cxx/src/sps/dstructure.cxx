#include "sps/dstructure.h"
#include "values.h"
#include "utils.h"
#include <boost/foreach.hpp>

VentureValuePtr SimplexOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  Simplex s;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    s.push_back(args->operandValues[i]->getDouble());
  }
  return VentureValuePtr(new VentureSimplex(s));
}

VentureValuePtr ToSimplexOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  Simplex s;
  double sum = 0;
  
  BOOST_FOREACH(VentureValuePtr v, args->operandValues[0]->getArray())
  {
    s.push_back(v->getDouble());
    sum += s.back();
  }
  
  for (size_t i = 0; i < s.size(); ++i)
  {
    s[i] /= sum;
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
  return VentureValuePtr(new VentureInteger(args->operandValues[0]->size()));
}

/* Dicts */

VentureValuePtr DictOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  MapVVPtrVVPtr d;
  vector<VentureValuePtr> syms = args->operandValues[0]->getArray();
  vector<VentureValuePtr> vals = args->operandValues[1]->getArray();
  if(syms.size() != vals.size()) throw "Dict must take equal numbers of keys and values.";
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
  checkArgsLength("prepend", args, 2);
  vector<VentureValuePtr> v;
  v.push_back(args->operandValues[0]);
  vector<VentureValuePtr> old = args->operandValues[1]->getArray();
  v.insert(v.end(), old.begin(), old.end());
  return VentureValuePtr(new VentureArray(v));
}

VentureValuePtr AppendOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("concat", args, 2);
  vector<VentureValuePtr> v(args->operandValues[0]->getArray());
  v.push_back(args->operandValues[1]);
  return VentureValuePtr(new VentureArray(v));
}

VentureValuePtr ConcatOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("append", args, 2);
  vector<VentureValuePtr> v1(args->operandValues[0]->getArray());
  const vector<VentureValuePtr>& v2 = args->operandValues[1]->getArray();
  v1.insert(v1.end(), v2.begin(), v2.end());
  return VentureValuePtr(new VentureArray(v1));
}

VentureValuePtr IsArrayOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("is_array", args, 1);
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
