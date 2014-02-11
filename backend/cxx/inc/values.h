#ifndef VALUES_H
#define VALUES_H

#include "srs.h"
#include "value.h"

struct VentureNumber : VentureValue
{
  VentureNumber(double x): x(x) {}
  double getDouble() const override { return x; }
  int getInt() const override { return static_cast<int>(x); }
  bool equals(shared_ptr<const VentureValue> & other) const override;
  size_t hash() const override;
  double x;

};

struct VentureAtom : VentureValue
{
  VentureAtom(int n): n(n) {}
  int getAtom() const override { return n; }
  bool equals(shared_ptr<const VentureValue> & other) const override;
  size_t hash() const override;
  int n;
};

struct VentureBool : VentureValue
{
  VentureBool(bool b): b(b) {}
  bool getBool() const override { return b; }
  bool equals(shared_ptr<const VentureValue> & other) const override;
  size_t hash() const override;
  bool b;
};

struct VentureSymbol : VentureValue
{
  VentureSymbol(string s): s(s) {}
  string getSymbol() const override { return s; }
  bool equals(shared_ptr<const VentureValue> & other) const override;
  size_t hash() const override;
  string s;
};

struct VentureArray : VentureValue
{
  VentureArray(const vector<VentureValuePtr> & xs): xs(xs) {}
  vector<VentureValuePtr> getArray() const override { return xs; }
  bool equals(shared_ptr<const VentureValue> & other) const override;
  size_t hash() const override;
  vector<VentureValuePtr> xs;
};

struct VentureNil : VentureValue
{
  bool isNil() const override { return true; }
  bool equals(shared_ptr<const VentureValue> & other) const override;
  size_t hash() const override;
};

struct VenturePair : VentureValue
{
  VenturePair(VentureValuePtr car,VentureValuePtr cdr) { car = car; cdr = cdr; }
  pair<VentureValuePtr,VentureValuePtr> getPair() const override { return make_pair(car,cdr); }
  bool equals(shared_ptr<const VentureValue> & other) const override;
  size_t hash() const override;
  VentureValuePtr car;
  VentureValuePtr cdr;
};

struct VentureSimplex : VentureValue
{
  VentureSimplex(const Simplex & ps): ps(ps) {}
  Simplex getSimplex() const override { return ps; }
  bool equals(shared_ptr<const VentureValue> & other) const override;
  size_t hash() const override;
  Simplex ps;
};

struct VentureDictionary : VentureValue
{
  // TODO need a special type with special hash/equality function.
  VentureDictionary(const unordered_map<VentureValuePtr,VentureValuePtr> & dict): dict(dict) {}
  unordered_map<VentureValuePtr,VentureValuePtr> getDictionary() const override { return dict; }
  unordered_map<VentureValuePtr,VentureValuePtr> dict;
};

struct VentureMatrix : VentureValue
{
  VentureMatrix(const Eigen::MatrixXd & m): m(m) {}
  MatrixXd getMatrix() const override { return m; }
  MatrixXd m;
};

struct VentureRequest : VentureValue
{
  VentureRequest(const vector<ESR> & esrs, const vector<shared_ptr<LSR> > & lsrs);
  vector<ESR> esrs;
  vector<shared_ptr<LSR> > lsrs;
};


#endif
