#ifndef LKERNEL_H
#define LKERNEL_H

#include "types.h"
#include "values.h"
#include <gsl/gsl_rng.h>
#include "args.h"

struct Trace;
struct Args;
struct PSP;
struct SP;
struct SPAux;


struct LKernel
{
  virtual VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng) =0;
  virtual double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args) { return 0; }
  virtual double reverseWeight(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args) 
    { 
      return weight(trace,oldValue,shared_ptr<VentureValue>(),args);
    }
  virtual std::pair<VentureValuePtr, vector<VentureValuePtr>> gradientOfReverseWeight(Trace * trace, VentureValuePtr value, shared_ptr<Args> args) 
    {
      vector<VentureValuePtr> gradients;
      for(auto ptr : args->operandValues) {
        gradients.push_back(VentureValuePtr(new VentureNumber(0)));
      }
      return make_pair(VentureValuePtr(new VentureNumber(0)), gradients);
    }
  virtual bool isIndependent() const { return true; }
};

struct DefaultAAALKernel : LKernel
{
  // TODO GC this kernel will not outlast the PSP
  DefaultAAALKernel(const PSP * makerPSP): makerPSP(makerPSP) {}

  VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng);
  double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args);

  const PSP * makerPSP;

};

struct DeterministicLKernel : LKernel
{
  DeterministicLKernel(VentureValuePtr value, shared_ptr<PSP> psp): value(value), psp(psp) {}

  VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng);
  double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args);
  std::pair<VentureValuePtr, vector<VentureValuePtr>> gradientOfReverseWeight(Trace * trace, VentureValuePtr value, shared_ptr<Args> args);
  VentureValuePtr value;
  shared_ptr<PSP> psp;
};

struct VariationalLKernel : LKernel
{
  virtual vector<double> gradientOfLogDensity(VentureValuePtr value, shared_ptr<Args> args) =0;
  virtual void updateParameters(Gradient gradient,double gain,double stepSize) =0;
};



#endif
