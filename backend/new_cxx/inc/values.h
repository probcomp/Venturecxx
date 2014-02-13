#ifndef VALUES_H
#define VALUES_H

#include "srs.h"
#include "value.h"

struct VentureNumber : VentureValue
{
  VentureNumber(double x): x(x) {}
  double getDouble() const { return x; }
  int getInt() const { return static_cast<int>(x); }
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  boost::python::dict toPython() const;

  double x;

};

struct VentureAtom : VentureValue
{
  VentureAtom(int n): n(n) {}
  int getAtom() const { return n; }
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  boost::python::dict toPython() const;
  int n;
};

struct VentureBool : VentureValue
{
  VentureBool(bool b): b(b) {}
  bool getBool() const { return b; }
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  boost::python::dict toPython() const;
  bool b;
};

struct VentureSymbol : VentureValue
{
  VentureSymbol(string s): s(s) {}
  const string& getSymbol() const { return s; }
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  string s;
};

struct VentureArray : VentureValue
{
  VentureArray(const vector<VentureValuePtr> & xs): xs(xs) {}
  const vector<VentureValuePtr> & getArray() const { return xs; }
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  vector<VentureValuePtr> xs;
};

struct VentureNil : VentureValue
{
  bool isNil() const { return true; }
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
};

struct VenturePair : VentureValue
{
  VenturePair(VentureValuePtr car,VentureValuePtr cdr) { car = car; cdr = cdr; }
  const VentureValuePtr& getCar() const { return car; }
  const VentureValuePtr& getCdr() const { return cdr; }
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  VentureValuePtr car;
  VentureValuePtr cdr;
};

struct VentureSimplex : VentureValue
{
  VentureSimplex(const Simplex & ps): ps(ps) {}
  const Simplex& getSimplex() const { return ps; }
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  Simplex ps;
};

struct VentureDictionary : VentureValue
{
  // TODO need a special type with special hash/equality function.
  VentureDictionary(const VentureValuePtrMap<VentureValuePtr> & dict): dict(dict) {}
  const VentureValuePtrMap<VentureValuePtr>& getDictionary() const { return dict; }
  VentureValuePtrMap<VentureValuePtr> dict;
};

struct VentureMatrix : VentureValue
{
  VentureMatrix(const Eigen::MatrixXd & m): m(m) {}
  const MatrixXd& getMatrix() const { return m; }
  MatrixXd m;
};

struct VentureRequest : VentureValue
{
  VentureRequest(const vector<ESR> & esrs, const vector<shared_ptr<LSR> > & lsrs): esrs(esrs), lsrs(lsrs) {}
  const vector<ESR>& getESRs() const { return esrs; }
  const vector<shared_ptr<LSR> >& getLSRs() const { return lsrs; }
  vector<ESR> esrs;
  vector<shared_ptr<LSR> > lsrs;
};

/* Use the memory location as a unique hash. */
struct VentureID {};

#endif
