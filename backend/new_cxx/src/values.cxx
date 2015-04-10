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

#include "values.h"
#include "utils.h"
#include "env.h"
#include "sprecord.h"
#include "Eigen/Dense"
#include <boost/lexical_cast.hpp>
#include <boost/foreach.hpp>
#include <boost/python/numeric.hpp>

using boost::lexical_cast;

//// Conversions

vector<VentureValuePtr> VenturePair::getArray() const
{
  vector<VentureValuePtr> xs;
  xs.push_back(getFirst());
  VentureValuePtr rest = getRest();
  shared_ptr<VenturePair> p;
  while (p = dynamic_pointer_cast<VenturePair>(rest))
  {
    xs.push_back(p->getFirst());
    rest = p->getRest();
  }
  // Permit improper lists whose tails are arrays to count as valid
  // Venture sequences.
  vector<VentureValuePtr> ys = rest->getArray();
  xs.insert(xs.end(), ys.begin(), ys.end());
  return xs;
}

vector<VentureValuePtr> VentureSimplex::getArray() const
{
  vector<VentureValuePtr> xs;
  for(size_t i = 0; i < ps.size(); ++i)
  {
    xs.push_back(VentureValuePtr(new VentureProbability(ps[i])));
  }
  return xs;
}

vector<VentureValuePtr> VentureVector::getArray() const
{
  vector<VentureValuePtr> xs;
  for(int i = 0; i < v.size(); ++i)
  {
    xs.push_back(VentureValuePtr(new VentureNumber(v(i))));
  }
  return xs;
}

MatrixXd VentureSimplex::getMatrix() const
{
  size_t len = ps.size();
  VectorXd v(len);

  for (size_t i = 0; i < len; ++i) { v(i) = ps[i]; }
  return v;
}

VectorXd VentureArray::getVector() const
{
  size_t len = xs.size();
  VectorXd v(len);
  for (size_t i = 0; i < len; ++i) { v(i) = xs[i]->getDouble(); }
  return v;
}

//// toPython methods

boost::python::dict VentureNumber::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "number";
  value["value"] = boost::python::object(x);
  return value;
}

boost::python::dict VentureInteger::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "integer";
  value["value"] = boost::python::object(n);
  return value;
}

boost::python::dict VentureProbability::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "probability";
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
  value["type"] = "boolean";
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

  boost::python::list l;
  l.append(getFirst()->toPython(trace));
  VentureValuePtr rest = getRest();
  shared_ptr<VenturePair> p;
  while (p = dynamic_pointer_cast<VenturePair>(rest))
  {
    l.append(p->getFirst()->toPython(trace));
    rest = p->getRest();
  }
  if (rest->isNil()) {
    value["type"] = "list";
    value["value"] = l;
  }
  else {
    value["type"] = "improper_list";
    value["value"] = boost::python::make_tuple(l, rest->toPython(trace));
  }
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
  boost::python::list items;
  
  BOOST_FOREACH(const MapVVPtrVVPtr::value_type& item, dict) {
    boost::python::object key = item.first->toPython(trace);
    boost::python::object val = item.second->toPython(trace);
    items.append(boost::python::make_tuple(key, val));
  }
  
  value["value"] = items;
  return value;
}

boost::python::dict VentureVector::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "vector";
  boost::python::list l;
  for (int i = 0; i < v.size(); ++i) { l.append(v(i)); }
  value["value"] = l;
  return value;
}

boost::python::dict VentureMatrix::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "matrix";
  // TODO convert directly without going through list
  boost::python::list l;
  for (int i = 0; i < m.rows(); ++i)
  {
    boost::python::list row;
    for (int j = 0; j < m.cols(); ++j) { row.append(m(i, j)); }
    l.append(row);
  }
  boost::python::numeric::array a(l);
  // set shape (needed for 0-length matrices)
  a.attr("shape") = boost::python::make_tuple(m.rows(), m.cols());
  value["value"] = a;
  return value;
}

boost::python::dict VentureSymmetricMatrix::toPython(Trace * trace) const
{
  boost::python::dict value = VentureMatrix::toPython(trace);
  value["type"] = "symmetric_matrix";
  return value;
}

//// Comparison methods

int VentureNumber::getValueTypeRank() const { return 0; }
int VentureInteger::getValueTypeRank() const { return 10; }
int VentureProbability::getValueTypeRank() const { return 20; }

int VentureAtom::getValueTypeRank() const { return 30; }
int VentureBool::getValueTypeRank() const { return 40; }
int VentureSymbol::getValueTypeRank() const { return 50; }

int VentureNil::getValueTypeRank() const { return 60; }
int VenturePair::getValueTypeRank() const { return 70; }
int VentureArray::getValueTypeRank() const { return 80; }
int VentureVector::getValueTypeRank() const { return 90; }

int VentureSimplex::getValueTypeRank() const { return 100; }
int VentureDictionary::getValueTypeRank() const { return 110; }
int VentureMatrix::getValueTypeRank() const { return 120; }
int VentureSymmetricMatrix::getValueTypeRank() const { return 130; }
int VentureSPRef::getValueTypeRank() const { return 140; }

int VentureEnvironment::getValueTypeRank() const { return 150; }
int VentureSPRecord::getValueTypeRank() const { return 160; }
int VentureRequest::getValueTypeRank() const { return 170; }
int VentureNode::getValueTypeRank() const { return 180; }
int VentureID::getValueTypeRank() const { return 190; }

bool VentureNumber::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureNumber> other_v = dynamic_pointer_cast<VentureNumber>(other);
  assert(other_v); return (x < other_v->x);
}

bool VentureInteger::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureInteger> other_v = dynamic_pointer_cast<VentureInteger>(other);
  assert(other_v); return (n < other_v->n);
}

bool VentureProbability::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureProbability> other_v = dynamic_pointer_cast<VentureProbability>(other);
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

bool VentureVector::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureVector> other_v = dynamic_pointer_cast<VentureVector>(other);
  assert(other_v);
  if (v.size() != other_v->v.size()) { return v.size() < other_v->v.size(); }
  for (int i = 0; i < v.size(); ++i)
    {
      if (v[i] < other_v->v[i]) { return true; }
      if (other_v->v[i] < v[i]) { return false; }
    }
  return false;
}

bool VentureMatrix::ltSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureMatrix> other_m = dynamic_pointer_cast<VentureMatrix>(other);
  assert(other_m);
  if (m.rows() != other_m->m.rows()) { return m.rows() < other_m->m.rows(); }
  if (m.cols() != other_m->m.cols()) { return m.cols() < other_m->m.cols(); }
  for (int i = 0; i < m.rows(); ++i)
    {
      for (int j = 0; j < m.cols(); ++j)
        {
          if (m(i, j) < other_m->m(i, j)) { return true; }
          if (other_m->m(i, j) < m(i, j)) { return false; }
        }
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

//// Equality methods

bool VentureNumber::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureNumber> other_v = dynamic_pointer_cast<VentureNumber>(other);
  assert(other_v); return (other_v->x == x);
}

bool VentureInteger::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureInteger> other_v = dynamic_pointer_cast<VentureInteger>(other);
  assert(other_v); return (other_v->n == n);
}

bool VentureProbability::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureProbability> other_v = dynamic_pointer_cast<VentureProbability>(other);
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

bool VentureSimplex::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureSimplex> other_v = dynamic_pointer_cast<VentureSimplex>(other);
  assert(other_v);
  if (ps.size() != other_v->ps.size()) { return false; }
  for (size_t i = 0; i < ps.size(); ++i) { if (ps[i] != other_v->ps[i]) { return false; } }
  return true;
}

bool VentureVector::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureVector> other_v = dynamic_pointer_cast<VentureVector>(other);
  assert(other_v);
  if (v.size() != other_v->v.size()) { return false; }
  for (int i = 0; i < v.size(); ++i) { if (v[i] != other_v->v[i]) { return false; } }
  return true;
}

bool VentureMatrix::equalsSameType(const VentureValuePtr & other) const
{
  shared_ptr<VentureMatrix> other_m = dynamic_pointer_cast<VentureMatrix>(other);
  assert(other_m);
  if (m.rows() != other_m->m.rows()) { return false; }
  if (m.cols() != other_m->m.cols()) { return false; }
  for (int i = 0; i < m.rows(); ++i)
    {
      for (int j = 0; j < m.cols(); ++j)
        {
          if (other_m->m(i, j) != m(i, j)) { return false; }
        }
    }
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

//// Hash methods

size_t VentureNumber::hash() const
{
  boost::hash<double> double_hash;
  return double_hash(x);
}

size_t VentureInteger::hash() const
{
  boost::hash<int> int_hash;
  return int_hash(n);
}

size_t VentureProbability::hash() const
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

size_t VentureArray::hash() const
{
  size_t seed = 0;

  BOOST_FOREACH (VentureValuePtr x,xs)
  {
    boost::hash_combine(seed, x->hash());
  }
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

//// toString methods

string VentureNumber::toString() const { return "VentureNumber " + lexical_cast<string>(x);}
string VentureInteger::toString() const { return "VentureInteger " + lexical_cast<string>(n);}
string VentureProbability::toString() const { return "VentureProbability " + lexical_cast<string>(x);}
string VentureAtom::toString() const { return "VentureAtom " + lexical_cast<string>(n);}
string VentureBool::toString() const { return "VentureBool " + lexical_cast<string>(b);}
string VentureSymbol::toString() const { return "VentureSymbol " + s;}
string VentureNil::toString() const { return "VentureNil";}
string VenturePair::toString() const { return "VenturePair (" + car->toString() + ", " + cdr->toString() + ")";}

string VentureArray::toString() const
{
  string s = "VentureArray [";
  for (size_t i = 0; i < xs.size(); ++i)
    {
      s += xs[i]->toString();
      s += " ";
    }
  s += "]";
  return s;
}

string VentureSimplex::toString() const { return "VentureSimplex";}
string VentureDictionary::toString() const { return "VentureDictionary";}
string VentureMatrix::toString() const { return "VentureMatrix";}
string VentureSymmetricMatrix::toString() const { return "VentureSymmetricMatrix";}

string VentureVector::toString() const
{
  string s = "VentureVector [";
  for (int i = 0; i < v.size(); ++i)
    {
      s += lexical_cast<string>(v(i));
      s += " ";
    }
  s += "]";
  return s;
}

string VentureRequest::toString() const { return "VentureRequest";}
string VentureNode::toString() const { return "VentureNode";}
string VentureID::toString() const { return "VentureID";}

//// asExpression methods

string VentureNumber::asExpression() const { return lexical_cast<string>(x);}
string VentureInteger::asExpression() const { return lexical_cast<string>(n);}
string VentureProbability::asExpression() const { return lexical_cast<string>(x);}
string VentureAtom::asExpression() const { return lexical_cast<string>(n);}
string VentureBool::asExpression() const { return lexical_cast<string>(b);}
string VentureSymbol::asExpression() const { return s;}
string VentureNil::asExpression() const { return "nil";}
string VenturePair::asExpression() const { return "[" + car->asExpression() + " . " + cdr->asExpression() + "]";}

string VentureArray::asExpression() const
{
  string s = "(";
  for (size_t i = 0; i < xs.size(); ++i)
    {
      s += xs[i]->asExpression();
      if (i + 1 < xs.size()) { s += " "; }
    }
  s += ")";
  return s;
}

string VentureSimplex::asExpression() const {
  string s = "(";
  for (size_t i = 0; i < ps.size(); ++i)
    {
      s += lexical_cast<string>(ps[i]);
      if (i + 1 < ps.size()) { s += " "; }
    }
  s += ")";
  return s;
}

///// Lookup methods

VentureValuePtr VenturePair::lookup(VentureValuePtr index) const
{
  if (index->getInt() == 0) { return car; }
  else { return cdr->lookup(VentureValuePtr(new VentureAtom(index->getInt() - 1))); }
}

VentureValuePtr VentureDictionary::lookup(VentureValuePtr index) const
{
  if (dict.count(index)) { return dict.at(index); }
  throw "Key " + index->toString() + " not found in VentureDictionary.";
}

VentureValuePtr VentureMatrix::lookup(VentureValuePtr index) const
{
  return VentureValuePtr(new VentureNumber(m(index->getFirst()->getInt(), index->getRest()->getInt())));
}

///// Contains methods

bool VenturePair::contains(VentureValuePtr item) const
{
  if (car->equals(item))
  {
    return true;
  } else {
    return cdr->contains(item);
  }
}

bool VentureArray::contains(VentureValuePtr item) const
{
  for (size_t i = 0; i < xs.size(); ++i)
  {
    if (xs[i]->equals(item)) { return true; }
  }
  return false;
}

bool VentureSimplex::contains(VentureValuePtr item) const
{
  double target = item->getDouble();
  for (size_t i = 0; i < ps.size(); ++i)
  {
    if (ps[i] == target) { return true; }
  }
  return false;
}

bool VentureVector::contains(VentureValuePtr item) const
{
  double target = item->getDouble();
  for (int i = 0; i < v.size(); ++i)
  {
    if (v[i] == target) { return true; }
  }
  return false;
}
