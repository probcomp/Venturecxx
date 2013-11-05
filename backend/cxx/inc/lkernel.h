#ifndef LKERNEL_H
#define LKERNEL_H

#include "omegadb.h"
#include "gsl/gsl_rng.h"

struct SP;

struct LKernel
{
  virtual VentureValue * simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB,gsl_rng * rng) =0;
  virtual double weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB) { return 0; };
  virtual double reverseWeight(VentureValue * oldVal, Node * appNode, LatentDB * latentDB)
    { return weight(oldVal,nullptr,appNode,latentDB); }

  bool isIndependent{true};

  virtual ~LKernel() {}
};

struct DefaultAAAKernel : LKernel
{
  DefaultAAAKernel(const SP * makerSP): makerSP(makerSP) {}

  VentureValue * simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB, gsl_rng * rng) override;
  double weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB) override;

  const SP * makerSP;

};

struct DeterministicLKernel : LKernel
{
  DeterministicLKernel(VentureValue * value, SP * sp): value(value), sp(sp) {}

  VentureValue * simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB,gsl_rng * rng) override;
  double weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB) override;

  VentureValue * value;
  SP * sp;
  
};

struct VariationalKernel : LKernel
{
  virtual double gradientOfLogDensity(VentureValue * output) { return 0; }
  virtual void updateParameters(double gradient) { }
};

#endif
