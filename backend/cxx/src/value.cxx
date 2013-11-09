#include "value.h"
#include "sp.h"

#include <iostream>
#include <boost/python/dict.hpp>

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

/* TODO FIXME Alexey can you sanity check this? It is massively rushed. */
size_t VenturePair::toHash() const
{
  size_t littlePrime = 37;
  size_t bigPrime = 12582917;

  return ((littlePrime * rest->toHash()) + first->toHash()) % bigPrime;

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
VentureValue * VentureSP::clone() const 
{ 
  VentureSP * vsp = new VentureSP(sp);
  vsp->makerNode = makerNode;
  return vsp;
}

// TODO FIXME MEMORY LEAK
// Right now this causes a minor memory leak--who cleans this up?
// Actually, cloning may always cause a memory leak, because generally only the outermost
// Value will be actually deleted. Unless values have a DEEP_DESTROY method.
VentureValue * VentureSymbol::inverseEvaluate() 
{ 
  return new VenturePair(new VentureSymbol("quote"), new VenturePair(this, new VentureNil));
}


VentureValue * VenturePair::inverseEvaluate() 
{ 
  return new VenturePair(new VentureSymbol("quote"), this);
}
