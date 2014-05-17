#include "values.h"
#include "utils.h"
#include "Eigen/Dense"
#include <boost/lexical_cast.hpp>
#include <boost/foreach.hpp>
#include <sstream>   

using std::stringstream;
using boost::lexical_cast;

/* TODO the constness in this file is incorrect, but I don't understand it well enough 
   yet, so I figure I will just play make-the-compiler-happy when the time comes.
*/
VentureValuePtrVector VentureNumber::getArray() const { 
  VentureValuePtrVector array;
  array.push_back(VentureNumber::makeValue(x));
  return array;
}

VentureValuePtr VentureNumber::makeValue(double x) {
  return VentureValuePtr(new VentureNumber(x));
}

VentureValuePtr VentureArray::makeValue(const VentureValuePtrVector & xs) {
  return VentureValuePtr(new VentureArray(xs));
}

VentureValuePtr VentureVector::makeValue(const VectorXd & xs) {
  return VentureValuePtr(new VentureVector(xs));
}

VentureValuePtr VentureMatrix::makeValue(const MatrixXd & xs) {
  return VentureValuePtr(new VentureMatrix(xs));
}

VentureValuePtr VentureArray::makeOnes(size_t length) {
  VentureValuePtrVector v;
  for(size_t i = 0; i < length; i++) {
    v.push_back(VentureNumber::makeValue(0));
  }
  return VentureValuePtr(new VentureArray(v));
}

VectorXd VentureArray::getVector() const { 
  VectorXd res(xs.size());
  for(int i = 0; i < xs.size(); i++) {
    shared_ptr<VentureNumber> v = dynamic_pointer_cast<VentureNumber>(xs[i]);
    assert(v != NULL);
    res[i] = v->getDouble();
  }
  return res;
}

VentureValuePtr VentureArray::makeZeros(size_t length) {
  return VentureArray::makeOnes(length)*VentureNumber::makeValue(0.0);
}

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
  for (size_t i = 0; i < ps.size(); ++i) { if (ps[i] != other_v->ps[i]) { return false; } }
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
string VentureArray::toString() const { 
  string str = "[";
  BOOST_FOREACH(VentureValuePtr x, xs) {
    str += x->toString()+" ";
  }
  str += "]";
  return "VentureArray\t"+str;
}
string VentureNil::toString() const { return "VentureNil";}
string VenturePair::toString() const { return "VenturePair (" + car->toString() + ", " + cdr->toString() + ")";}
string VentureSimplex::toString() const { return "VentureSimplex";}
string VentureDictionary::toString() const { return "VentureDictionary";}
string VentureMatrix::toString() const { return "VentureMatrix";}
string VentureVector::toString() const { 
  stringstream str;
  str << "[";
  for(int i = 0; i < v.size(); i++) {
    str << v(i) << " ";
  }
  str << "]";
  return "VentureVector\t"+str.str();
}
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

boost::python::dict VentureVector::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "vector";
  boost::python::list l;
  for (size_t i = 0; i < v.size(); ++i) { l.append(v(i)); }
  value["value"] = l;
  return value;
}

boost::python::dict VentureMatrix::toPython(Trace * trace) const
{
  boost::python::dict value;
  value["type"] = "matrix";
  boost::python::list l;
  for (size_t i = 0; i < m.rows(); ++i)
  {
    boost::python::list row;
    for (size_t j = 0; j < m.cols(); ++j) { row.append(m(i, j)); }
    l.append(row);
  }
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
  value["value"] = toPythonDict(trace, dict);
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

VentureValuePtr VentureNumber::operator+(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureNumber> rhsVal = dynamic_pointer_cast<VentureNumber>(rhs);
  assert(rhsVal != NULL);
  return VentureValuePtr(new VentureNumber(this->x+rhsVal->x));
}

VentureValuePtr VentureArray::operator+(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureArray> rhsVal = dynamic_pointer_cast<VentureArray>(rhs);
  assert(rhsVal != NULL);
  const vector<VentureValuePtr> rhsVector = rhsVal->getArray();
  vector<VentureValuePtr> newVector;
  assert(rhsVector.size() == this->xs.size());
  for(int i = 0; i < rhsVector.size(); i++) {
    newVector.push_back(rhsVector[i]+xs[i]);
  }
  return VentureValuePtr(new VentureArray(newVector));
}

VentureValuePtr VentureVector::operator+(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureVector> rhsVal = dynamic_pointer_cast<VentureVector>(rhs);
  assert(rhsVal != NULL);
  assert(this->v.size() == rhsVal->v.size());
  VectorXd x(v.size());
  for (int i = 0; i < v.size(); ++i) { 
    x(i) = v(i)+rhsVal->v(i);
  }
  return VentureVector::makeValue(x);
}

VentureValuePtr VentureMatrix::operator+(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureMatrix> rhsVal = dynamic_pointer_cast<VentureMatrix>(rhs);
  assert(rhsVal != NULL);
  assert(this->m.size() == rhsVal->m.size());
  VectorXd x(m.rows(), m.cols());
  for (int i = 0; i < m.rows(); ++i) { 
    for(int j = 0; j < m.cols(); ++j) {
      x(i,j) = m(i,j)+rhsVal->m(i,j);
    }
  }
  return VentureMatrix::makeValue(x);
}

VentureValuePtr VentureNumber::operator-(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureNumber> rhsVal = dynamic_pointer_cast<VentureNumber>(rhs);
  assert(rhsVal != NULL);
  return VentureValuePtr(new VentureNumber(this->x-rhsVal->x));
}

VentureValuePtr VentureArray::operator-(const VentureValuePtr & rhs) const {
  // cout << "venture array rhs = " << ::toString(rhs) << endl;
  const shared_ptr<VentureArray> rhsVal = dynamic_pointer_cast<VentureArray>(rhs);
  assert(rhsVal != NULL);
  const vector<VentureValuePtr> rhsVector = rhsVal->getArray();
  vector<VentureValuePtr> newVector;
  assert(rhsVector.size() == this->xs.size());
  for(int i = 0; i < rhsVector.size(); i++) {
    newVector.push_back(xs[i]-rhsVector[i]);
  }
  return VentureValuePtr(new VentureArray(newVector));
}

VentureValuePtr VentureVector::operator-(const VentureValuePtr & rhs) const {
  // cout << "rhs = " << ::toString(rhs) << endl;
  const shared_ptr<VentureVector> rhsVal = dynamic_pointer_cast<VentureVector>(rhs);
  assert(rhsVal != NULL);
  assert(this->v.size() == rhsVal->v.size());
  VectorXd x(v.size());
  for (int i = 0; i < v.size(); ++i) { 
    x(i) = v(i)-rhsVal->v(i);
  }
  return VentureVector::makeValue(x);
}

VentureValuePtr VentureMatrix::operator-(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureMatrix> rhsVal = dynamic_pointer_cast<VentureMatrix>(rhs);
  assert(rhsVal != NULL);
  assert(this->m.size() == rhsVal->m.size());
  VectorXd x(m.rows(), m.cols());
  for (int i = 0; i < m.rows(); ++i) { 
    for(int j = 0; j < m.cols(); ++j) {
      x(i,j) = m(i,j)-rhsVal->m(i,j);
    }
  }
  return VentureMatrix::makeValue(x);
}

VentureValuePtr VentureNumber::operator*(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureNumber> rhsVal = dynamic_pointer_cast<VentureNumber>(rhs);
  assert(rhsVal != NULL);
  return VentureValuePtr(new VentureNumber(this->x*rhsVal->x));
}

VentureValuePtr VentureArray::operator*(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureNumber> rhsVal = dynamic_pointer_cast<VentureNumber>(rhs);
  if(rhsVal != NULL) { // product by a number.
    vector<VentureValuePtr> newVector;
    for(int i = 0; i < xs.size(); i++) {
      newVector.push_back(xs[i]*rhsVal);
    }
    return VentureValuePtr(new VentureArray(newVector));  
  }
  const shared_ptr<VentureArray> rhsArray = dynamic_pointer_cast<VentureArray>(rhs); 
  if(rhsArray != NULL) { // product by a vector.
    const vector<VentureValuePtr> rhsVector = rhsArray->getArray();
    vector<VentureValuePtr> newVector;
    for(int i = 0; i < rhsVector.size(); i++) {
      newVector.push_back(rhsVector[i]*xs[i]);
    }
    return VentureValuePtr(new VentureArray(newVector));  
  }
  throw "other implementation of operator * not supported.";
}

VentureValuePtr VentureVector::operator*(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureNumber> rhsValNum = dynamic_pointer_cast<VentureNumber>(rhs);
  if(rhsValNum != NULL) { // product by a number.
    VectorXd x(v.size());
    for(int i = 0; i < v.size(); i++) {
      x(i) = v(i)*rhsValNum->getDouble();
    }
    return VentureVector::makeValue(x);  
  }
  const shared_ptr<VentureVector> rhsVal = dynamic_pointer_cast<VentureVector>(rhs);
  assert(rhsVal != NULL);
  assert(this->v.size() == rhsVal->v.size());
  VectorXd x(v.size());
  for (int i = 0; i < v.size(); ++i) { 
    x(i) = v(i)*rhsVal->v(i);
  }
  return VentureVector::makeValue(x);
}


VentureValuePtr VentureMatrix::operator*(const VentureValuePtr & rhs) const {
  const shared_ptr<VentureMatrix> rhsVal = dynamic_pointer_cast<VentureMatrix>(rhs);
  assert(rhsVal != NULL);
  assert(this->m.size() == rhsVal->m.size());
  VectorXd x(m.rows(), m.cols());
  for (int i = 0; i < m.rows(); ++i) { 
    for(int j = 0; j < m.cols(); ++j) {
      x(i,j) = m(i,j)*rhsVal->m(i,j);
    }
  }
  return VentureMatrix::makeValue(x);
}

VentureValuePtr VentureNumber::neg() const {
  return VentureNumber::makeValue(this->x);
}

VentureValuePtr VentureVector::neg() const {
  VectorXd x(v.size());
  for (int i = 0; i < v.size(); ++i) { 
    x(i) = 0-v(i);
  }
  return VentureVector::makeValue(x);
}

VentureValuePtr VentureArray::neg() const {
  vector<VentureValuePtr> newVector;
  for(int i = 0; i < xs.size(); i++) {
    newVector.push_back(xs[i]->neg());
  }
  return VentureArray::makeValue(newVector);
}

VentureValuePtr VentureMatrix::neg() const {
  VectorXd x(m.rows(), m.cols());
  for (int i = 0; i < m.rows(); ++i) { 
    for(int j = 0; j < m.cols(); ++j) {
      x(i,j) = 0-m(i,j);
    }
  }
  return VentureMatrix::makeValue(x);
}

double VentureBool::getDouble() const {
  return (double)b;
}
