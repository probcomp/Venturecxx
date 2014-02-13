#ifndef VALUE_H
#define VALUE_H

#include "types.h"
#include "srs.h"
#include <vector>
#include "Eigen/Dense"

#include <boost/python/object.hpp>
#include <boost/python/dict.hpp>
#include <boost/unordered_map.hpp>

using Eigen::MatrixXd;
using Eigen::VectorXd;

using std::vector;
using std::pair;

struct HashVentureValuePtr;
struct VentureValuePtrsEqual;

template <typename T>
class VentureValuePtrMap : boost::unordered_map<VentureValuePtr, T, HashVentureValuePtr, VentureValuePtrsEqual> {};

// TODO AXCH
// We need to be more consistent about whether this unboxes
// TODO optimization: return const&
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
  virtual Simplex getSimplex() const;
  virtual const VentureValuePtrMap<VentureValuePtr>& getDictionary() const;
  virtual MatrixXd getMatrix() const;
  virtual pair<vector<ESR>,vector<shared_ptr<LSR> > > getRequests() const;

  virtual boost::python::dict toPython() const { assert(false); throw "need to override toPython()"; };

  virtual bool equals(const shared_ptr<const VentureValue> & other) const;
  virtual size_t hash() const;
};

/* for unordered map */
struct VentureValuePtrsEqual
{
  bool operator() (const VentureValuePtr& a, const VentureValuePtr& b)
  {
    return a->equals(b);
  }
};

struct HashVentureValuePtr
{
  size_t operator() (const VentureValuePtr& a)
  {
    return a->hash();
  }
};

#endif
