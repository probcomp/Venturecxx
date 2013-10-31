#ifndef LKERNEL_H
#define LKERNEL_H

#include "omegadb.h"
#include "gsl/gsl_rng.h"

struct LKernel
{
  virtual VentureValue * simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB,gsl_rng * rng) const =0;
  virtual double weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB) const =0;
  virtual double reverseWeight(VentureValue * oldVal, Node * appNode, LatentDB * latentDB) const =0;
};

struct LIndependentKernel : LKernel {};
struct LDeltaKernel : LKernel {};

#endif
