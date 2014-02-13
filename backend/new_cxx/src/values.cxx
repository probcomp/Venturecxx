#include "values.h"
#include "Eigen/Dense"

/* TODO the constness in this file is incorrect, but I don't understand it well enough 
   yet, so I figure I will just play make-the-compiler-happy when the time comes.
*/
   
bool VentureNumber::equals(const shared_ptr<const VentureValue> & other) const
{
  shared_ptr<const VentureNumber> other_v = dynamic_pointer_cast<const VentureNumber>(other);
  return other_v && (other_v->x == x);
}

bool VentureAtom::equals(const shared_ptr<const VentureValue> & other) const
{
  shared_ptr<const VentureAtom> other_v = dynamic_pointer_cast<const VentureAtom>(other);
  return other_v && (other_v->n == n);
}

bool VentureBool::equals(const shared_ptr<const VentureValue> & other) const
{
  shared_ptr<const VentureBool> other_v = dynamic_pointer_cast<const VentureBool>(other);
  return other_v && (other_v->b == b);
}

bool VentureSymbol::equals(const shared_ptr<const VentureValue> & other) const
{
  shared_ptr<const VentureSymbol> other_v = dynamic_pointer_cast<const VentureSymbol>(other);
  return other_v && (other_v->s == s);
}

bool VentureArray::equals(const shared_ptr<const VentureValue> & other) const
{
  shared_ptr<const VentureArray> other_v = dynamic_pointer_cast<const VentureArray>(other);
  if (!other_v) { return false; }
  if (xs.size() != other_v->xs.size()) { return false; }
  for (size_t i = 0; i < xs.size(); ++i) 
  { 
    if (!xs[i]->equals(other_v->xs[i])) { return false; } 
  }
  return true;
}

bool VentureNil::equals(const shared_ptr<const VentureValue> & other) const
{
  shared_ptr<const VentureNil> other_v = dynamic_pointer_cast<const VentureNil>(other);
  return other_v;
}

bool VenturePair::equals(const shared_ptr<const VentureValue> & other) const
{
  shared_ptr<const VenturePair> other_v = dynamic_pointer_cast<const VenturePair>(other);
  if (!other_v) { return false; }
  return (other_v->car->equals(car) && other_v->cdr->equals(cdr));
}

bool VentureSimplex::equals(const shared_ptr<const VentureValue> & other) const
{
  shared_ptr<const VentureSimplex> other_v = dynamic_pointer_cast<const VentureSimplex>(other);
  if (!other_v) { return false; }
  if (ps.size() != other_v->ps.size()) { return false; }
  for (size_t i = 0; i < ps.size(); ++i) { if (!ps[i] == other_v->ps[i]) { return false; } }
  return true;
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
