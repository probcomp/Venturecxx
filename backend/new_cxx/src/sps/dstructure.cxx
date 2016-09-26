// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "sps/dstructure.h"
#include "values.h"
#include "utils.h"
#include "env.h" // For the request in ArrayMapRequestPSP
#include "expressions.h" // For the request in ArrayMapRequestPSP
#include "sp.h" // For VentureSPRef in FixRequestPSP
#include <boost/foreach.hpp>
#include <boost/range/combine.hpp>

VentureValuePtr SimplexOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  Simplex s;
  for (size_t i = 0; i < args->operandValues.size(); ++i) {
    s.push_back(args->operandValues[i]->getDouble());
  }
  return VentureValuePtr(new VentureSimplex(s));
}

VentureValuePtr ToSimplexOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  Simplex s;
  double sum = 0;

  BOOST_FOREACH(VentureValuePtr v, args->operandValues[0]->getArray()) {
    s.push_back(v->getDouble());
    sum += s.back();
  }

  for (size_t i = 0; i < s.size(); ++i) {
    s[i] /= sum;
  }

  return VentureValuePtr(new VentureSimplex(s));
}


VentureValuePtr IsSimplexOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureSimplex>(args->operandValues[0]) != NULL));
}


/* Polymorphic operators */

VentureValuePtr LookupOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return args->operandValues[0]->lookup(args->operandValues[1]);
}

VentureValuePtr ContainsOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(args->operandValues[0]->contains(args->operandValues[1])));
}


VentureValuePtr SizeOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureInteger(args->operandValues[0]->size()));
}

/* Dicts */

VentureValuePtr DictOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  MapVVPtrVVPtr d;
  for (size_t i = 0; i < args->operandValues.size(); ++i) {
    VentureValuePtr key = args->operandValues[i]->lookup(VentureValuePtr(new VentureNumber(0)));
    VentureValuePtr val = args->operandValues[i]->lookup(VentureValuePtr(new VentureNumber(1)));
    d[key] = val;
  }
  return VentureValuePtr(new VentureDictionary(d));
}

VentureValuePtr IsDictOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureDictionary>(args->operandValues[0]) != NULL));
}



/* Arrays */

VentureValuePtr ArrayOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureArray(args->operandValues));
}

VentureValuePtr ToArrayOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  vector<VentureValuePtr> a;

  BOOST_FOREACH(VentureValuePtr v, args->operandValues[0]->getArray()) {
    a.push_back(v);
  }

  return VentureValuePtr(new VentureArray(a));
}

VentureValuePtr PrependOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("prepend", args, 2);
  vector<VentureValuePtr> v;
  v.push_back(args->operandValues[0]);
  vector<VentureValuePtr> old = args->operandValues[1]->getArray();
  v.insert(v.end(), old.begin(), old.end());
  return VentureValuePtr(new VentureArray(v));
}

VentureValuePtr AppendOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("concat", args, 2);
  vector<VentureValuePtr> v(args->operandValues[0]->getArray());
  v.push_back(args->operandValues[1]);
  return VentureValuePtr(new VentureArray(v));
}

VentureValuePtr ConcatOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("append", args, 2);
  vector<VentureValuePtr> v1(args->operandValues[0]->getArray());
  const vector<VentureValuePtr>& v2 = args->operandValues[1]->getArray();
  v1.insert(v1.end(), v2.begin(), v2.end());
  return VentureValuePtr(new VentureArray(v1));
}

VentureValuePtr IsArrayOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("is_array", args, 1);
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureArray>(args->operandValues[0]) != NULL));
}


/* Lists */

VentureValuePtr PairOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("pair", args, 2);
  return VentureValuePtr(new VenturePair(args->operandValues[0], args->operandValues[1]));
}

VentureValuePtr IsPairOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VenturePair>(args->operandValues[0]) != NULL));
}


VentureValuePtr ListOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  VentureValuePtr l(new VentureNil());
  for (size_t i = args->operandValues.size(); i > 0; --i) {
    l = VentureValuePtr(new VenturePair(args->operandValues[i-1], l));
  }
  return l;
}

VentureValuePtr FirstOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return args->operandValues[0]->getFirst();
}

VentureValuePtr SecondOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return args->operandValues[0]->getRest()->getFirst();
}


VentureValuePtr RestOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return args->operandValues[0]->getRest();
}


/* Functional */

VentureValuePtr ApplyRequestPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  VentureValuePtr optor = args->operandValues[0];
  VentureValuePtr opands = args->operandValues[1];

  shared_ptr<VentureEnvironment> env =
    shared_ptr<VentureEnvironment>(new VentureEnvironment());

  vector<VentureValuePtr> parts;
  parts.push_back(quote(optor));
  BOOST_FOREACH(VentureValuePtr opand, opands->getArray()) {
    parts.push_back(quote(opand));
  }
  VentureValuePtr expression = VentureValuePtr(new VentureArray(parts));
  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureID()), expression, env));
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}


VentureValuePtr FixRequestPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("fix", args, 2);

  VentureValuePtr ids = args->operandValues[0];
  VentureValuePtr expressions = args->operandValues[1];
  shared_ptr<VentureEnvironment> env =
    shared_ptr<VentureEnvironment>(new VentureEnvironment(args->env));
  BOOST_FOREACH(VentureValuePtr id, ids->getArray()) {
    env->addBinding(id->getSymbol(), NULL);
  }
  vector<ESR> esrs;
  BOOST_FOREACH(VentureValuePtr expression, expressions->getArray()) {
    esrs.push_back(ESR(VentureValuePtr(new VentureID()), expression, env));
  }
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}

VentureValuePtr FixOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  vector<VentureValuePtr> ids = args->operandValues[0]->getArray();
  shared_ptr<VentureEnvironment> env = args->env;
  BOOST_FOREACH(ESR esr, args->requestValue->esrs) {
    assert(env == args->env || env == esr.env);
    env = esr.env;
  }
  for (size_t i = 0; i < ids.size(); ++i) {
    env->fillBinding(ids[i]->getSymbol(), args->esrParentNodes[i].get());
  }
  return env;
}

VentureValuePtr ArrayMapRequestPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  VentureValuePtr optor = args->operandValues[0];
  VentureValuePtr opands = args->operandValues[1];

  shared_ptr<VentureEnvironment> env =
    shared_ptr<VentureEnvironment>(new VentureEnvironment());

  vector<ESR> esrs;
  BOOST_FOREACH(VentureValuePtr opand, opands->getArray()) {
    vector<VentureValuePtr> parts;
    parts.push_back(quote(optor));
    parts.push_back(quote(opand));
    VentureValuePtr expression = VentureValuePtr(new VentureArray(parts));
    esrs.push_back(ESR(VentureValuePtr(new VentureID()), expression, env));
  }
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}

VentureValuePtr IndexedArrayMapRequestPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  VentureValuePtr optor = args->operandValues[0];
  VentureValuePtr opands = args->operandValues[1];

  shared_ptr<VentureEnvironment> env =
    shared_ptr<VentureEnvironment>(new VentureEnvironment());

  vector<ESR> esrs;
  BOOST_FOREACH(VentureValuePtr opand, opands->getArray()) {
    vector<VentureValuePtr> parts;
    parts.push_back(quote(optor));
    parts.push_back(VentureValuePtr(new VentureNumber((double)esrs.size()))); // The index
    parts.push_back(quote(opand));
    VentureValuePtr expression = VentureValuePtr(new VentureArray(parts));
    esrs.push_back(ESR(VentureValuePtr(new VentureID()), expression, env));
  }
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}

VentureValuePtr ESRArrayOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureArray(args->esrParentValues));
}

VentureValuePtr ArangeOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  long start = args->operandValues[0]->getInt();
  long end = args->operandValues[1]->getInt();
  vector<VentureValuePtr> items;
  for (long i = start; i < end; i++) {
    items.push_back(VentureValuePtr(new VentureInteger(i)));
  }
  return VentureValuePtr(new VentureArray(items));
}

VentureValuePtr RepeatOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  long ct = args->operandValues[0]->getInt();
  double item = args->operandValues[1]->getDouble();
  VectorXd v(ct);
  for (int i = 0; i < ct; ++i) { v(i) = item; }
  return VentureValuePtr(new VentureVector(v));
}
