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
  return sp->name;
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
  const VentureValue * vfirst = dynamic_cast<const VentureValue*>(vp->first);
  const VentureValue * vrest = dynamic_cast<const VentureValue*>(vp->rest);
  
  return vp && first->equals(vfirst) && rest->equals(vrest);
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
  const VentureVector * vv = dynamic_cast<const VentureVector*>(other);
  if (vv->xs.size() != xs.size()) { return false; }
  for (size_t i = 0; i < xs.size(); ++i)
  {
    const VentureValue * v = dynamic_cast<const VentureValue*>(vv->xs[i]);
    if (!xs[i]->equals(v)) { return false; }
  }
  return true;
}

void deepDelete(VentureValue * value)
{
  value->destroyParts();
  delete value;
}
