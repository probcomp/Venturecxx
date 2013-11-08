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
