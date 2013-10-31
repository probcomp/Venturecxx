#ifndef GKERNEL_H
#define GKERNEL_H

#include <stdint.h>
#include "trace.h"

struct MixMHParam {  virtual ~MixMHParam() {} };

struct GKernel
{
  GKernel(Trace * trace): trace(trace) {}

  virtual double propose() =0;
  virtual void accept() =0;
  virtual void reject() =0;

  void infer(uint32_t N);

  Trace * trace;
};

struct GKernelMaker
{
  GKernelMaker(Trace * trace): trace(trace) {}
  virtual GKernel * constructGKernel(MixMHParam * param) =0;
  Trace * trace;
};

struct MixMHIndex { virtual ~MixMHIndex() {} };

struct MixMHKernel : GKernel
{
  MixMHKernel(Trace * trace, GKernelMaker * gKernelMaker):
    GKernel(trace), gKernelMaker(gKernelMaker) {}

  virtual MixMHIndex * sampleIndex() =0;
  virtual double logDensityOfIndex(MixMHIndex * index) =0;
  virtual MixMHParam * processIndex(MixMHIndex * index) =0;
  
  double propose();
  void accept()  { childGKernel->accept(); }
  void reject()  { childGKernel->reject(); }

  GKernelMaker * gKernelMaker;

  /* constructed anew for each proposal */
  GKernel * childGKernel; 
};
#endif
