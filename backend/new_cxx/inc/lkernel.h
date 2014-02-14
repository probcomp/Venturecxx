#ifndef LKERNEL_H
#define LKERNEL_H

#include "types.h"
#include <gsl/gsl_rng.h>

struct Trace;
struct Args;
struct PSP;
struct VentureSP;

struct LKernel
{
  virtual VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng) =0;
  virtual double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args) { return 0; }
  virtual double reverseWeight(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args) 
    { 
      return weight(trace,oldValue,shared_ptr<VentureValue>(),args);
    }
  virtual bool isIndependent() const { return true; }
};

struct DefaultAAALKernel : LKernel
{
  DefaultAAALKernel(const shared_ptr<VentureSP> makerSP): makerSP(makerSP) {}

  VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng);
  double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args);

  const shared_ptr<VentureSP> makerSP;

};

struct DeterministicLKernel : LKernel
{
  DeterministicLKernel(VentureValuePtr value, shared_ptr<PSP> psp): value(value), psp(psp) {}

  VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng);
  double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args);

  VentureValuePtr value;
  shared_ptr<PSP> psp;
  
};





#endif
