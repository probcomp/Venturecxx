#ifndef VALUES_H
#define VALUES_H

#include "srs.h"
#include "value.h"


struct VentureNumber : VentureValue
{
  VentureNumber(double x): x(x) {}
  VentureValuePtrVector getArray() const;
  static VentureValuePtr makeValue(double x); // factory.
  bool hasDouble() const { return true; }
  double getDouble() const { return x; }
  bool hasInt() const { return false; }
  long getInt() const { return static_cast<int>(x); }
  bool getBool() const { return x; }
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;
  size_t hash() const;
  boost::python::dict toPython(Trace * trace) const;
  string toString() const;
  VentureValuePtr operator+(const VentureValuePtr & rhs) const;
  VentureValuePtr operator-(const VentureValuePtr & rhs) const;
  VentureValuePtr operator*(const VentureValuePtr & rhs) const;
  VentureValuePtr neg() const;
  double x;
};

struct VentureAtom : VentureValue
{
  VentureAtom(int n): n(n) {}
  bool hasDouble() const { return true; }
  double getDouble() const { return n; }
  bool hasInt() const { return false; }
  long getInt() const { return n; }
  int getAtom() const { return n; }
  bool getBool() const { return n; }
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  size_t hash() const;
  boost::python::dict toPython(Trace * trace) const;
  string toString() const;
  int n;
};

struct VentureBool : VentureValue
{
  VentureBool(bool b): b(b) {}
  bool isBool() const { return true; }
  bool getBool() const { return b; }
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  size_t hash() const;
  boost::python::dict toPython(Trace * trace) const;
  string toString() const;
  bool b;
};

struct VentureSymbol : VentureValue
{
  VentureSymbol(string s): s(s) {}
  bool hasSymbol() const { return true; }
  const string& getSymbol() const { return s; }
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  boost::python::dict toPython(Trace * trace) const;
  size_t hash() const;
  string toString() const;
  string s;
};

struct VentureArray : VentureValue
{
  VentureArray(const VentureValuePtrVector & xs): xs(xs) {}
  VentureValuePtrVector getArray() const { return xs; }
  VectorXd getVector() const;
  static VentureValuePtr makeValue(const VentureValuePtrVector & xs);
  static VentureValuePtr makeOnes(size_t length);
  static VentureValuePtr makeZeros(size_t length);
  VentureValuePtr lookup(VentureValuePtr index) const { return xs[index->getInt()]; }
  int size() const { return xs.size(); }
  boost::python::dict toPython(Trace * trace) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  bool hasArray() const { return true; }
  size_t hash() const;
  VentureValuePtrVector xs;
  string toString() const;
  VentureValuePtr operator+(const VentureValuePtr & rhs) const;
  VentureValuePtr operator-(const VentureValuePtr & rhs) const;
  VentureValuePtr operator*(const VentureValuePtr & rhs) const;
  VentureValuePtr neg() const;
};

struct VentureNil : VentureValue
{
  bool isNil() const { return true; }
  VentureValuePtr lookup(VentureValuePtr index) const { cout << "lookup in nil" << endl; assert(false); }
  int size() const { return 0; }
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  bool hasArray() const { return true; }
  VentureValuePtrVector getArray() const { return VentureValuePtrVector(); }

  size_t hash() const;
  string toString() const;
  boost::python::dict toPython(Trace * trace) const;
};

struct VenturePair : VentureValue
{
  VenturePair(VentureValuePtr car,VentureValuePtr cdr): car(car), cdr(cdr) { }
  const VentureValuePtr& getFirst() const { return car; }
  const VentureValuePtr& getRest() const { return cdr; }
  VentureValuePtr lookup(VentureValuePtr index) const;
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  bool hasArray() const { return true; }
  VentureValuePtrVector getArray() const;

  size_t hash() const;
  string toString() const;
  boost::python::dict toPython(Trace * trace) const;
  int size() const { return 1 + getRest()->size(); }
  VentureValuePtr car;
  VentureValuePtr cdr;
};

struct VentureSimplex : VentureValue
{
  VentureSimplex(const Simplex & ps): ps(ps) {}
  const Simplex& getSimplex() const { return ps; }
  MatrixXd getMatrix() const;
  int size() const { return ps.size(); }
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  size_t hash() const;
  string toString() const;
  boost::python::dict toPython(Trace * trace) const;
  Simplex ps;
};

struct VentureDictionary : VentureValue
{
  // TODO need a special type with special hash/equality function.
  VentureDictionary(const VentureValuePtrMap<VentureValuePtr> & dict): dict(dict) {}
  const VentureValuePtrMap<VentureValuePtr>& getDictionary() const { return dict; }

  VentureValuePtr lookup(VentureValuePtr index) const { return dict.at(index); }
  bool contains(VentureValuePtr index) const { return dict.count(index); }
  int size() const { return dict.size(); }


  boost::python::dict toPython(Trace * trace) const;
  string toString() const;
  VentureValuePtrMap<VentureValuePtr> dict;
};

struct VentureMatrix : VentureValue
{
  VentureMatrix(const Eigen::MatrixXd & m): m(m) {}
  static VentureValuePtr makeValue(const MatrixXd & xs);
  MatrixXd getMatrix() const { return m; }
  string toString() const;
  boost::python::dict toPython(Trace * trace) const;
  MatrixXd m;
  VentureValuePtr operator+(const VentureValuePtr & rhs) const;
  VentureValuePtr operator-(const VentureValuePtr & rhs) const;
  VentureValuePtr operator*(const VentureValuePtr & rhs) const; // pointwise product.
  VentureValuePtr neg() const;
};

struct VentureVector : VentureValue
{
  VentureVector(const Eigen::VectorXd & v): v(v) {}
  static VentureValuePtr makeValue(const VectorXd & xs);
  VentureValuePtr lookup(VentureValuePtr index) const { return VentureValuePtr(new VentureNumber(v(index->getInt()))); }
  VectorXd getVector() const { return v; }
  boost::python::dict toPython(Trace * trace) const;
  VectorXd v;
  string toString() const;
  VentureValuePtr operator+(const VentureValuePtr & rhs) const;
  VentureValuePtr operator-(const VentureValuePtr & rhs) const;
  VentureValuePtr operator*(const VentureValuePtr & rhs) const;
  VentureValuePtr neg() const;
};

struct VentureRequest : VentureValue
{
  VentureRequest(const vector<ESR> & esrs, const vector<shared_ptr<LSR> > & lsrs): esrs(esrs), lsrs(lsrs) {}
  VentureRequest(const vector<ESR> & esrs): esrs(esrs) {}
  VentureRequest(const vector<shared_ptr<LSR> > & lsrs): lsrs(lsrs) {}

  const vector<ESR>& getESRs() const { return esrs; }
  const vector<shared_ptr<LSR> >& getLSRs() const { return lsrs; }
  string toString() const;
  vector<ESR> esrs;
  vector<shared_ptr<LSR> > lsrs;
};


struct VentureNode : VentureValue
{
  VentureNode(Node * node): node(node) {}
  bool hasInt() const { return true; }
  long getInt() const { return reinterpret_cast<long>(node); }

  bool hasNode() const { return true; }
  Node * getNode() const { return node; }
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  string toString() const;
  size_t hash() const;
  Node * node;
};

/* Use the memory location as a unique hash. */
struct VentureID : VentureValue
{
  bool hasInt() const { return true; }
  long getInt() const { return reinterpret_cast<long>(this); }
  bool equalsSameType(const VentureValuePtr & other) const;
  bool ltSameType(const VentureValuePtr & other) const;

  size_t hash() const;
  string toString() const;
};

#endif
