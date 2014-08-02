/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "value.h"
#include "sp.h"

#include <iostream>
#include <boost/python/dict.hpp>

VentureValue::~VentureValue()
{
  assert(isValid()); 
  magic = 0;
}

VentureSP::~VentureSP() 
{ 
  delete sp; 
}


size_t VentureSymbol::toHash() const 
{ 
  return hash<string>()(sym); 
}

bool VentureSymbol::equals(const VentureValue * & other) const 
{ 
  const VentureSymbol * vsym = dynamic_cast<const VentureSymbol*>(other);
  return vsym && vsym->sym == sym;
}

string VentureSP::toString() const
{
  return "sp:" + sp->name;
}

boost::python::dict VentureValue::toPython() const
{ 
  boost::python::dict value;
  value["type"] = "generic";
  value["value"] = boost::python::object();
  return value;
}

boost::python::dict VentureSymbol::toPython() const
{ 
  boost::python::dict value;
  value["type"] = "symbol";
  value["value"] = boost::python::object(sym);
  return value;
}

boost::python::dict VentureNumber::toPython() const
{ 
  boost::python::dict value;
  value["type"] = "number";
  value["value"] = boost::python::object(x);
  return value;
}

boost::python::dict VentureAtom::toPython() const
{ 
  boost::python::dict value;
  value["type"] = "atom";
  value["value"] = boost::python::object(n);
  return value;
}

boost::python::dict VentureBool::toPython() const
{ 
  boost::python::dict value;
  value["type"] = "boolean";
  value["value"] = boost::python::object(pred);
  return value;
}

boost::python::dict VentureNil::toPython() const
{ 
  boost::python::dict value;
  value["type"] = "list";
  value["value"] = boost::python::list();
  return value;
}

boost::python::dict VenturePair::toPython() const
{ 
  boost::python::dict value;
  value["type"] = "list";
  boost::python::list l;
  l.append(first->toPython());
  l.extend(rest->toPython()["value"]);
  value["value"] = l;
  return value;
}

boost::python::dict VentureVector::toPython() const
{
  boost::python::dict value;
  value["type"] = "vector";
  boost::python::list l;
  for (VentureValue * x : xs) { l.append(x->toPython()); }
  value["value"] = l;
  return value;
}

boost::python::dict VentureMatrix::toPython() const 
{
  boost::python::dict value;
  value["type"] = "matrix";
  boost::python::list l;
  for (VentureVector * x : xs) {l.append(x->toPython()); }
  value["value"] = l;
  return value;
}

boost::python::dict VentureSP::toPython() const
{ 
  boost::python::dict value;
  value["type"] = "sp";
  value["value"] = boost::python::object("sp");
  return value;
}

size_t VentureNil::toHash() const
{
  size_t mediumPrime = 24593;
  return mediumPrime;
}

/* TODO FIXME Alexey can you sanity check this? It is rushed. */
size_t VenturePair::toHash() const
{
  size_t seed = rest->toHash();
  boost::hash_combine(seed, first->toHash());
  return seed;
}

VentureValue * VentureNil::clone() const { return new VentureNil; }
VentureValue * VenturePair::clone() const 
{ 
  VentureValue * f = first->clone();
  VentureList * r = dynamic_cast<VentureList*>(rest->clone());
  assert(r);
  return new VenturePair(f,r);
}

VentureValue * VentureSymbol::clone() const { return new VentureSymbol(sym); }
VentureValue * VentureBool::clone() const { return new VentureBool(pred); }
VentureValue * VentureNumber::clone() const { return new VentureNumber(x); }
VentureValue * VentureAtom::clone() const { return new VentureAtom(n); }

// I forget if this breaks something or not
// TODO check the incremental_evaluator again
VentureValue * VentureSP::clone() const 
{ 
  VentureSP * vsp = new VentureSP(sp);
  vsp->makerNode = makerNode;
  return vsp;
}

void VenturePair::destroyParts()
{
  deepDelete(first);
  deepDelete(rest);
}

void VentureVector::destroyParts()
{
  for (VentureValue * x : xs)
  {
    deepDelete(x);
  }
}

size_t VentureVector::toHash() const 
{
  size_t seed = 0;

  for (VentureValue * x : xs) 
  { 
    boost::hash_combine(seed, x->toHash());
  }
  return seed;
}

void VentureMatrix::destroyParts() 
{
  for(VentureVector * x : xs) 
  {
    deepDelete(x);
  }
}

size_t VentureMatrix::toHash() const 
{
  size_t seed = 0;
  for (VentureVector * x : xs) {
    boost::hash_combine(seed, x->toHash());
  }
  return seed;
}


bool VentureBool::equals(const VentureValue * & other) const
{
  const VentureBool * vb = dynamic_cast<const VentureBool*>(other);
  return vb && vb->pred == pred;
}

bool VentureNil::equals(const VentureValue * & other) const
{
  const VentureNil * vn = dynamic_cast<const VentureNil*>(other);
  return vn;
}

bool VenturePair::equals(const VentureValue * & other) const
{
  const VenturePair * vp = dynamic_cast<const VenturePair*>(other);
  if (!vp) { return false; }

  const VentureValue * vfirst = dynamic_cast<const VentureValue*>(vp->first);
//  const VentureList * vrest = dynamic_cast<const VentureList*>(vp->rest);
  const VentureValue * vrest = dynamic_cast<const VentureValue*>(vp->rest);
  assert(vfirst);
  assert(vrest);
  return first->equals(vfirst) && rest->equals(vrest);
}

bool VentureNumber::equals(const VentureValue * & other) const
{
  const VentureNumber * vn = dynamic_cast<const VentureNumber*>(other);
  return vn && vn->x == x;
}

// TODO atom == number?
bool VentureAtom::equals(const VentureValue * & other) const
{
  const VentureAtom * va = dynamic_cast<const VentureAtom*>(other);
  return va && va->n == n;
}

bool VentureVector::equals(const VentureValue * & other) const
{
  // sanity check: dynamic_cast would return null if it's a bad cast.
  const VentureVector * vv = dynamic_cast<const VentureVector*>(other);
  if (vv->xs.size() != xs.size()) { return false; }
  for (size_t i = 0; i < xs.size(); ++i)
  {
    const VentureValue * v = dynamic_cast<const VentureValue*>(vv->xs[i]);
    if (!xs[i]->equals(v)) { return false; }
  }
  return true;
}

bool VentureMatrix::equals(const VentureValue * & other) const 
{
  const VentureMatrix * vv = dynamic_cast<const VentureMatrix*>(other);
  if (vv == NULL || vv->xs.size() != xs.size()) return false;
  for(size_t i = 0; i < xs.size(); i++) {
    const VentureValue * v = dynamic_cast<const VentureValue*>(vv->xs[i]);
    if(!xs[i]->equals(v)) return false;
  }
  return true;
}

void deepDelete(VentureValue * value)
{
  value->destroyParts();
  delete value;
}

string VentureBool::toString() const
{
  if (pred) { return "#t"; }
  else { return "#f"; }
}

string VentureNumber::toString() const
{
  return to_string(x);
}

string VentureAtom::toString() const
{
  return to_string(n);
}

string VentureRequest::toString() const
{
  string s = "[";
  bool first = true;
  for (ESR esr : esrs)
  {
    if (!first) { s += ", "; }
    s += "(" + to_string(esr.id) + ", " + esr.exp->toString() + ", <env>)";
    first = false;
  }
  s += "]";
  return s;
}

string VentureSymbol::toString() const { return sym; }

string VentureNil::toString()  const
{ 
  return "()"; 
}

string VenturePair::toString()  const
{ 
  assert(first);
  string s = "(" + first->toString();
  VentureList * l = rest;
  assert(l);
  while (!dynamic_cast<VentureNil*>(l))
  {
    VenturePair * pair = dynamic_cast<VenturePair*>(l);
    assert(pair);
    assert(pair->first);
    // TODO except for rendering, would probably want a comma here
    s += " " + pair->first->toString();
    l = pair->rest;
  }
  s += ")";
  return s; 
}
