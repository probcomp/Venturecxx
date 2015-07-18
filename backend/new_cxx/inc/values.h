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

#ifndef VALUES_H
#define VALUES_H

#include "srs.h"
#include "value.h"


struct VentureNumber : VentureValue
{
  VentureNumber(double x): x(x) {}

  bool hasDouble() const { return true; }
  double getDouble() const { return x; }
  bool hasInt() const { return false; }
  long getInt() const { return static_cast<int>(x); }
  bool getBool() const { return x; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
  string asExpression() const;

  double x;
};

struct VentureInteger : VentureValue
{
  VentureInteger(int n): n(n) {}

  bool hasDouble() const { return true; }
  double getDouble() const { return n; }
  bool hasInt() const { return true; }
  long getInt() const { return n; }
  bool getBool() const { return n; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
  string asExpression() const;

  int n;
};

struct VentureProbability : VentureValue
{
  VentureProbability(double x): x(x) {}

  bool hasDouble() const { return true; }
  double getDouble() const { return x; }
  double getProbability() const { return x; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
  string asExpression() const;

  double x;
};

struct VentureAtom : VentureValue
{
  VentureAtom(int n): n(n) {}

  bool hasDouble() const { return true; }
  double getDouble() const { return n; }
  bool hasInt() const { return true; }
  long getInt() const { return n; }
  int getAtom() const { return n; }
  bool getBool() const { return n; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
  string asExpression() const;

  int n;
};

struct VentureBool : VentureValue
{
  VentureBool(bool b): b(b) {}

  bool isBool() const { return true; }
  bool getBool() const { return b; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
  string asExpression() const;

  bool b;
};

struct VentureSymbol : VentureValue
{
  VentureSymbol(string s): s(s) {}

  bool hasSymbol() const { return true; }
  const string& getSymbol() const { return s; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
  string asExpression() const;

  string s;
};

struct VentureString : VentureValue
{
  VentureString(string s): s(s) {}

  bool hasString() const { return true; }
  const string& getString() const { return s; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
  string asExpression() const;

  string s;
};

struct VentureNil : VentureValue
{
  bool isNil() const { return true; }
  bool hasArray() const { return true; }
  vector<VentureValuePtr> getArray() const { return vector<VentureValuePtr>(); }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  VentureValuePtr lookup(VentureValuePtr index) const { throw "Tried to lookup in nil or list index out of range"; }
  bool contains(VentureValuePtr index) const { return false; }
  int size() const { return 0; }

  string toString() const;
  string asExpression() const;
};

struct VenturePair : VentureValue
{
  VenturePair(VentureValuePtr car,VentureValuePtr cdr): car(car), cdr(cdr) { }

  const VentureValuePtr& getFirst() const { return car; }
  const VentureValuePtr& getRest() const { return cdr; }
  bool hasArray() const { return true; }
  vector<VentureValuePtr> getArray() const;

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  VentureValuePtr lookup(VentureValuePtr index) const;
  bool contains(VentureValuePtr index) const;
  int size() const { return 1 + getRest()->size(); }

  string toString() const;
  string asExpression() const;

  VenturePair* copy_help(ForwardingMap* m) const;

  VentureValuePtr car;
  VentureValuePtr cdr;
};

struct VentureArray : VentureValue
{
  VentureArray(const vector<VentureValuePtr> & xs): xs(xs) {}

  bool hasArray() const { return true; }
  vector<VentureValuePtr> getArray() const { return xs; }
  VectorXd getVector() const; // Only if it's homogeneous and all numbers

  boost::python::dict toPython(Trace * trace) const;

  VentureValuePtr lookup(VentureValuePtr index) const { return xs[index->getInt()]; }
  bool contains(VentureValuePtr index) const;
  int size() const { return xs.size(); }

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
  string asExpression() const;

  VentureArray* copy_help(ForwardingMap* m) const;

  vector<VentureValuePtr> xs;
};

struct VentureSimplex : VentureValue
{
  VentureSimplex(const Simplex & ps): ps(ps) {}

  vector<VentureValuePtr> getArray() const;
  const Simplex& getSimplex() const { return ps; }
  MatrixXd getMatrix() const;

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  VentureValuePtr lookup(VentureValuePtr index) const { return VentureValuePtr(new VentureProbability(ps[index->getInt()])); }
  bool contains(VentureValuePtr index) const;
  int size() const { return ps.size(); }

  string toString() const;
  string asExpression() const;

  Simplex ps;
};

struct VentureDictionary : VentureValue
{
  // TODO need a special type with special hash/equality function.
  VentureDictionary(const MapVVPtrVVPtr & dict): dict(dict) {}

  const MapVVPtrVVPtr& getDictionary() const { return dict; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;

  VentureValuePtr lookup(VentureValuePtr index) const;
  bool contains(VentureValuePtr index) const { return dict.count(index); }
  int size() const { return dict.size(); }

  string toString() const;

  VentureDictionary* copy_help(ForwardingMap* m) const;

  MapVVPtrVVPtr dict;
};

struct VentureMatrix : VentureValue
{
  VentureMatrix(const Eigen::MatrixXd & m): m(m) {}

  MatrixXd getMatrix() const { return m; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;

  VentureValuePtr lookup(VentureValuePtr index) const;

  string toString() const;

  MatrixXd m;
};

struct VentureSymmetricMatrix : VentureMatrix
{
  VentureSymmetricMatrix(const Eigen::MatrixXd & m): VentureMatrix(m) {}

  MatrixXd getSymmetricMatrix() const { return m; }

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;

  string toString() const;
};

struct VentureVector : VentureValue
{
  VentureVector(const Eigen::VectorXd & v): v(v) {}

  VectorXd getVector() const { return v; }
  bool hasArray() const { return true; }
  vector<VentureValuePtr> getArray() const;

  boost::python::dict toPython(Trace * trace) const;

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;

  VentureValuePtr lookup(VentureValuePtr index) const { return VentureValuePtr(new VentureNumber(v(index->getInt()))); }
  bool contains(VentureValuePtr index) const;
  int size() const { return v.size(); }

  string toString() const;

  VectorXd v;
};

struct VentureRequest : VentureValue
{
  VentureRequest(const vector<ESR> & esrs, const vector<boost::shared_ptr<LSR> > & lsrs): esrs(esrs), lsrs(lsrs) {}
  VentureRequest(const vector<ESR> & esrs): esrs(esrs) {}
  VentureRequest(const vector<boost::shared_ptr<LSR> > & lsrs): lsrs(lsrs) {}

  int getValueTypeRank() const;

  const vector<ESR>& getESRs() const { return esrs; }
  const vector<boost::shared_ptr<LSR> >& getLSRs() const { return lsrs; }

  string toString() const;

  vector<ESR> esrs;
  vector<boost::shared_ptr<LSR> > lsrs;
};


struct VentureNode : VentureValue
{
  VentureNode(Node * node): node(node) {}

  bool hasInt() const { return true; }
  long getInt() const { return reinterpret_cast<long>(node); }

  bool hasNode() const { return true; }
  Node * getNode() const { return node; }

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;

  VentureNode* copy_help(ForwardingMap* m) const;

  Node * node;
};

/* Use the memory location as a unique hash. */
struct VentureID : VentureValue
{
  bool hasInt() const { return true; }
  long getInt() const { return reinterpret_cast<long>(this); }

  int getValueTypeRank() const;
  bool ltSameType(const VentureValuePtr & other) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  size_t hash() const;

  string toString() const;
};

#endif
