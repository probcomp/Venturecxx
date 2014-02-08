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
  double getDouble();
  int getInt();
  int getAtom();
  bool getBool();
  string getSymbol();
  vector<VentureValuePtr> getArray();
  pair<VentureValuePtr,VentureValuePtr> getPair();
  simplex getSimplex();
  map<VentureValuePtr,VentureValuePtr> getDict();
  MatrixXd getMatrix();
  VentureSPPtr getSP();
  VentureEnvironmentPtr getEnvironment();
  pair<vector<ESR>,vector<LSR *> > getRequests();
};


#endif
