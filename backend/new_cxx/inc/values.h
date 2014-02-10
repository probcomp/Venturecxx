#ifndef VALUES_H
#define VALUES_H

struct VentureNumber : VentureValue
{
  VentureNumber(double x): x(x) {}
  double getDouble() { return x; }
  int getInt() { return static_cast<int>(x); }
  double x;
};

struct VentureAtom : VentureValue
{
  VentureAtom(int n): n(n) {}
  int getAtom() { return n; }
  int n;
};

struct VentureBool : VentureValue
{
  VentureBool(bool b): b(b) {}
  bool getBool() { return b; }
  bool b;
};

struct VentureSymbol : VentureValue
{
  VentureSymbol(string s): s(s) {}
  string getSymbol() { return s; }
  string s;
};

struct VentureArray : VentureValue
{
  VentureArray(const vector<VentureValuePtr> & xs): xs(xs) {}
  vector<VentureValuePtr> getArray() { return xs; }
  vector<VentureValuePtr> xs;
};

struct VentureNil : VentureValue
{
  bool isNil() { return true; }
};

struct VenturePair : VentureValue
{
  VenturePair(VentureValuePtr car,VentureValuePtr cdr): car(car),cdr(cdr) {}
  pair<VentureValuePtr,VentureValuePtr> getPair() { return make_pair(car,cdr); }
  VentureValuePtr car;
  VentureValuePtr cdr;
};

struct VentureSimplex : VentureValue
{
  VentureSimplex(const simplex & p): p(p) {}
  simplex getSimplex() { return p; }
  simplex p;
};

struct VentureDictionary : VentureValue
{
  // TODO need a special type with special hash/equality function.
  VentureDictionary(const unordered_map<VentureValuePtr,VentureValuePtr> & dict): dict(dict) {}
  unordered_map<VentureValuePtr,VentureValuePtr> getDictionary() { return dict; }
  unordered_map<VentureValuePtr,VentureValuePtr> dict;
};

struct VentureMatrix : VentureValue
{
  VentureMatrix(const MatrixXd & m): m(m) {}
  MatrixXd getMatrix() { return m; }
  MatrixXd m;
};


#endif
