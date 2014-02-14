#include "values.h"
#include "Eigen/Dense"
#include <boost/lexical_cast.hpp>

using boost::lexical_cast;

/* TODO the constness in this file is incorrect, but I don't understand it well enough 
   yet, so I figure I will just play make-the-compiler-happy when the time comes.
*/
   
bool VentureNumber::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureNumber> other_v = dynamic_pointer_cast<VentureNumber>(other);
  return other_v && (other_v->x == x);
}

bool VentureAtom::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureAtom> other_v = dynamic_pointer_cast<VentureAtom>(other);
  return other_v && (other_v->n == n);
}

bool VentureBool::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureBool> other_v = dynamic_pointer_cast<VentureBool>(other);
  return other_v && (other_v->b == b);
}

bool VentureSymbol::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureSymbol> other_v = dynamic_pointer_cast<VentureSymbol>(other);
  return other_v && (other_v->s == s);
}

bool VentureArray::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureArray> other_v = dynamic_pointer_cast<VentureArray>(other);
  if (!other_v) { return false; }
  if (xs.size() != other_v->xs.size()) { return false; }
  for (size_t i = 0; i < xs.size(); ++i) 
  { 
    if (!xs[i]->equals(other_v->xs[i])) { return false; } 
  }
  return true;
}

bool VentureNil::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureNil> other_v = dynamic_pointer_cast<VentureNil>(other);
  return other_v;
}

bool VenturePair::equals(const VentureValuePtr & other) const
{
  shared_ptr<VenturePair> other_v = dynamic_pointer_cast<VenturePair>(other);
  if (!other_v) { return false; }
  return (other_v->car->equals(car) && other_v->cdr->equals(cdr));
}

bool VentureSimplex::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureSimplex> other_v = dynamic_pointer_cast<VentureSimplex>(other);
  if (!other_v) { return false; }
  if (ps.size() != other_v->ps.size()) { return false; }
  for (size_t i = 0; i < ps.size(); ++i) { if (!ps[i] == other_v->ps[i]) { return false; } }
  return true;
}

bool VentureNode::equals(const VentureValuePtr & other) const
{
  return dynamic_pointer_cast<VentureNode>(other) && node == other->getNode();
}

bool VentureID::equals(const VentureValuePtr & other) const
{
  return this == other.get();
}

//////////////////////////////////////

size_t VentureNumber::hash() const 
{ 
  boost::hash<double> double_hash;
  return double_hash(x);
}

size_t VentureAtom::hash() const
{ 
  boost::hash<int> int_hash;
  return int_hash(n);
}

size_t VentureBool::hash() const
{ 
  boost::hash<bool> bool_hash;
  return bool_hash(b);
}

size_t VentureSymbol::hash() const
{ 
  boost::hash<string> string_hash;
  return string_hash(s);
}

size_t VentureArray::hash() const
{ 
  return boost::hash_range(xs.begin(),xs.end());
}

size_t VentureNil::hash() const
{ 
  return 3491; // TODO arbitrary prime
}

size_t VenturePair::hash() const
{ 
  size_t seed = 0;
  boost::hash_combine(seed, car);
  boost::hash_combine(seed, cdr);
  return seed;
}

size_t VentureSimplex::hash() const
{ 
  return boost::hash_range(ps.begin(),ps.end());
}

size_t VentureNode::hash() const
{
  return reinterpret_cast<size_t>(node);
}

size_t VentureID::hash() const
{
  return reinterpret_cast<size_t>(this);
}

/* toString methods */

string VentureNumber::toString() const { return "VentureNumber " + lexical_cast<string>(x);}
string VentureAtom::toString() const { return "VentureAtom " + lexical_cast<string>(n);}
string VentureBool::toString() const { return "VentureBool " + lexical_cast<string>(b);}
string VentureSymbol::toString() const { return "VentureSymbol " + s;}
string VentureArray::toString() const { return "VentureArray";}
string VentureNil::toString() const { return "VentureNil";}
string VenturePair::toString() const { return "VenturePair (" + car->toString() + ", " + cdr->toString() + ")";}
string VentureSimplex::toString() const { return "VentureSimplex";}
string VentureDictionary::toString() const { return "VentureDictionary";}
string VentureMatrix::toString() const { return "VentureMatrix";}
string VentureRequest::toString() const { return "VentureRequest";}
string VentureNode::toString() const { return "VentureNode";}
string VentureID::toString() const { return "VentureID";}

//////////////

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
  value["type"] = "bool";
  value["value"] = boost::python::object(b);
  return value;
}
