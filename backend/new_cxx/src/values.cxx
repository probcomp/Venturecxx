#include "values.h"
#include "Eigen/Dense"
#include <boost/lexical_cast.hpp>
#include <boost/foreach.hpp>

using boost::lexical_cast;

/* TODO the constness in this file is incorrect, but I don't understand it well enough 
   yet, so I figure I will just play make-the-compiler-happy when the time comes.
*/
   
bool VentureNumber::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureNumber> other_v = dynamic_pointer_cast<VentureNumber>(other);
  assert(other_v); return (other_v->x == x);
}

bool VentureAtom::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureAtom> other_v = dynamic_pointer_cast<VentureAtom>(other);
  assert(other_v); return (other_v->n == n);
}

bool VentureBool::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureBool> other_v = dynamic_pointer_cast<VentureBool>(other);
  assert(other_v); return (other_v->b == b);
}

bool VentureSymbol::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureSymbol> other_v = dynamic_pointer_cast<VentureSymbol>(other);
  assert(other_v); return (other_v->s == s);
}

bool VentureArray::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureArray> other_v = dynamic_pointer_cast<VentureArray>(other);
  assert(other_v);
  if (xs.size() != other_v->xs.size()) { return false; }
  for (size_t i = 0; i < xs.size(); ++i) 
  { 
    if (!xs[i]->equals(other_v->xs[i])) 
    { 
      return false; 
    } 
  }
  return true;
}

bool VentureNil::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureNil> other_v = dynamic_pointer_cast<VentureNil>(other);
  assert(other_v);
  return true;
}

bool VenturePair::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VenturePair> other_v = dynamic_pointer_cast<VenturePair>(other);
  assert(other_v);
  return (other_v->car->equals(car) && other_v->cdr->equals(cdr));
}

bool VentureSimplex::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureSimplex> other_v = dynamic_pointer_cast<VentureSimplex>(other);
  assert(other_v);
  if (ps.size() != other_v->ps.size()) { return false; }
  for (size_t i = 0; i < ps.size(); ++i) { if (!ps[i] == other_v->ps[i]) { return false; } }
  return true;
}

bool VentureNode::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureNode> other_v = dynamic_pointer_cast<VentureNode>(other);
  assert(other_v);
  return node == other_v->getNode();
}

bool VentureID::equalsSameType(const VentureValuePtr & other) const
{
  return this == other.get();
}

//////////////////////////////////////
bool VentureNumber::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureNumber> other_v = dynamic_pointer_cast<VentureNumber>(other);
  assert(other_v); return (x < other_v->x);
}

bool VentureAtom::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureAtom> other_v = dynamic_pointer_cast<VentureAtom>(other);
  assert(other_v); return (n < other_v->n);
}

bool VentureBool::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureBool> other_v = dynamic_pointer_cast<VentureBool>(other);
  assert(other_v); return (b < other_v->b);
}

bool VentureSymbol::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureSymbol> other_v = dynamic_pointer_cast<VentureSymbol>(other);
  assert(other_v); return (s < other_v->s);
}

bool VentureArray::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureArray> other_v = dynamic_pointer_cast<VentureArray>(other);
  assert(other_v);
  if (xs.size() != other_v->xs.size()) { return xs.size() < other_v->xs.size(); }
  for (size_t i = 0; i < xs.size(); ++i) 
  { 
    if (xs[i] < other_v->xs[i]) { return true; }
    if (other_v->xs[i] < xs[i]) { return false; }
  }
  return false;
}

bool VentureNil::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureNil> other_v = dynamic_pointer_cast<VentureNil>(other);
  assert(other_v);
  return false;
}

bool VenturePair::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VenturePair> other_v = dynamic_pointer_cast<VenturePair>(other);
  assert(other_v);
  if (car < other_v->car) { return true; }
  else if (other_v->car < car) { return false; }
  else { return (cdr < other_v->cdr); }
}

bool VentureSimplex::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureSimplex> other_v = dynamic_pointer_cast<VentureSimplex>(other);
  assert(other_v);
  if (ps.size() != other_v->ps.size()) { return ps.size() < other_v->ps.size(); }
  for (size_t i = 0; i < ps.size(); ++i) 
    {
      if (ps[i] < other_v->ps[i]) { return true; } 
      if (other_v->ps[i] < ps[i]) { return false; } 
    }
  return false;
}

bool VentureNode::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureNode> other_v = dynamic_pointer_cast<VentureNode>(other);
  assert(other_v);
  return node < other_v->node;
}

bool VentureID::ltSameType(const VentureValuePtr & other) const
{
  return this < other.get();
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
  size_t seed = 0;

  BOOST_FOREACH (VentureValuePtr x,xs)
  { 
    boost::hash_combine(seed, x->hash());
  }
  return seed;
}

size_t VentureNil::hash() const
{ 
  return 3491; // TODO arbitrary prime
}

size_t VenturePair::hash() const
{ 
  size_t seed = 0;
  boost::hash_combine(seed, car->hash());
  boost::hash_combine(seed, cdr->hash());
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

/* toPython methods */

boost::python::dict VentureNumber::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "number";
  value["value"] = boost::python::object(x);
  return value;
}

boost::python::dict VentureAtom::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "atom";
  value["value"] = boost::python::object(n);
  return value;
}
boost::python::dict VentureBool::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "bool";
  value["value"] = boost::python::object(b);
  return value;
}

boost::python::dict VentureSymbol::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "symbol";
  value["value"] = boost::python::object(s);
  return value;
}

boost::python::dict VentureArray::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "array";
  boost::python::list l;
  for (size_t i = 0; i < xs.size(); ++i) { l.append(xs[i]->toPython(trace)); }
  value["value"] = l;
  return value;
}

boost::python::dict VentureSimplex::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "simplex";
  boost::python::list l;
  for (size_t i = 0; i < ps.size(); ++i) { l.append(ps[i]); }
  value["value"] = l;
  return value;
}

boost::python::dict VentureDictionary::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "dict";
  value["value"] = boost::python::object(false); // TODO
  return value;
}

boost::python::dict VentureNil::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "list";
  boost::python::list l;
  value["value"] = l;
  return value;
}


boost::python::dict VenturePair::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "list";

  boost::python::list l;
  l.append(getFirst()->toPython(trace));
  shared_ptr<VenturePair>  p = dynamic_pointer_cast<VenturePair>(getRest());
  while (p)
  {
    l.append(p->getFirst()->toPython(trace));
    p = dynamic_pointer_cast<VenturePair>(p->getRest());
  }
  value["value"] = l;
  return value;
}


/* Lookup */
VentureValuePtr VenturePair::lookup(VentureValuePtr index) const
{
  if (index->getInt() == 0) { return car; }
  else { return cdr->lookup(VentureValuePtr(new VentureAtom(index->getInt() - 1))); }
}

////////////  
MatrixXd VentureSimplex::getMatrix() const
{
  size_t len = ps.size();
  VectorXd v(len);

  for (size_t i = 0; i < len; ++i) { v(i) = ps[i]; }
  return v;
}

/////////////
vector<VentureValuePtr> VenturePair::getArray() const
{
  // TODO Make this not be quadratic
  // The reason it's done this way is to permit improper lists whose
  // tails are arrays to count as valid Venture sequences.
  VentureValuePtr v(getRest());
  vector<VentureValuePtr> answer = v->getArray();
  answer.insert(answer.begin(), getFirst());
  return answer;
}
