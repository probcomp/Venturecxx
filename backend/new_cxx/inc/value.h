#ifndef VALUE_H
#define VALUE_H

#include "types.h"
#include <vector>
#include <pair>
#include "Eigen/Dense"

using std::vector;
using std::pair;

// TODO AXCH
// We need to be more consistent about whether this unboxes
struct VentureValue
{
  virtual double getDouble() const;
  virtual int getInt() const;
  virtual int getAtom() const;
  virtual bool getBool() const;
  virtual string getSymbol() const;
  virtual vector<VentureValuePtr> getArray() const;
  virtual bool isNil() const { return false; }
  virtual pair<VentureValuePtr,VentureValuePtr> getPair() const;
  virtual simplex getSimplex() const;
  virtual map<VentureValuePtr,VentureValuePtr> getDictionary() const;
  virtual MatrixXd getMatrix() const;
  virtual pair<vector<ESR>,vector<LSR *> > getRequests() const;

  virtual bool equals(const VentureValue * & other) const;
  virtual size_t hash() const;
};

/* For unordered_map. */
bool operator==(shared_ptr<const VentureValue> & a, shared_ptr<const VentureValue> & b)
{
  return a->equals(b);
}

/* For unordered map. */
size_t hash_value(shared_ptr<const VentureValue> & a)
{
  return a->hash();
}

#endif
