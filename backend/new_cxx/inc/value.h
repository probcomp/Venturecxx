#ifndef VALUE_H
#define VALUE_H

#include "types.h"
#include "srs.h"
#include <vector>
#include "Eigen/Dense"

#include <boost/python/object.hpp>
#include <boost/python/dict.hpp>

using Eigen::MatrixXd;
using Eigen::VectorXd;

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
  virtual Simplex getSimplex() const;
  virtual unordered_map<VentureValuePtr,VentureValuePtr> getDictionary() const;
  virtual MatrixXd getMatrix() const;
  virtual pair<vector<ESR>,vector<LSR * > > getRequests() const;

  virtual boost::python::dict toPython() const { assert(false); throw "need to override toPython()"; };

  virtual bool equals(const shared_ptr<const VentureValue> & other) const;
  virtual size_t hash() const;
};

/* for unordered map */
/*
namespace boost {
  template <>
  bool operator==(const shared_ptr<const VentureValue> & a, const shared_ptr<const VentureValue> & b)
  {
    return a->equals(b);
  }

  template <>
  size_t hash_value(const shared_ptr<const VentureValue> & a)
  {
    return a->hash();
  }
}
*/
#endif
