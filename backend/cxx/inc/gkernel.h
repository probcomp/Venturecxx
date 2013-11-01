#ifndef GKERNEL_H
#define GKERNEL_H

#include <stdint.h>

using namespace std;

struct Trace;

struct MixMHParam {  virtual ~MixMHParam() {} };

struct GKernel
{
  GKernel(Trace * trace): trace(trace) {}

  virtual double propose() =0;
  virtual void accept() =0;
  virtual void reject() =0;

  virtual ~GKernel() {}

  void infer(uint32_t N);

  Trace * trace;

};

struct GKernelMaker
{
  GKernelMaker(Trace * trace): trace(trace) {}
  virtual GKernel * constructGKernel(MixMHParam * param) =0;
  Trace * trace;

  virtual ~GKernelMaker() { }
};


struct MixMHIndex { virtual ~MixMHIndex() {} };

struct MixMHKernel : GKernel
{
  MixMHKernel(Trace * trace, GKernelMaker * gKernelMaker):
    GKernel(trace), gKernelMaker(gKernelMaker) {}

  virtual MixMHIndex * sampleIndex() =0;
  virtual double logDensityOfIndex(MixMHIndex * index) =0;
  virtual MixMHParam * processIndex(MixMHIndex * index) =0;
  
  double propose() override;
  void accept() override { childGKernel->accept(); reset(); }
  void reject() override { childGKernel->reject(); reset(); }
  
  void reset() { delete index; delete param; delete childGKernel; }
  
  GKernelMaker * gKernelMaker;

  /* constructed anew for each proposal */
  MixMHIndex * index;
  MixMHParam * param;
  GKernel * childGKernel; 
};
#endif
