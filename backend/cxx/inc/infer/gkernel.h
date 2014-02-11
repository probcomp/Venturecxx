#ifndef GKERNEL_H
#define GKERNEL_H

#include "check.h"
#include <stdint.h>

using namespace std;

struct Trace;

struct MixMHIndex { virtual ~MixMHIndex() {} };

/* processIndex(index) => param may be non-injective */
struct MixMHParam {  virtual ~MixMHParam() {} };

struct GKernel
{
  GKernel(Trace * trace): trace(trace) {}

  virtual double propose() =0;
  virtual void accept() =0;
  virtual void reject() =0;

  virtual void destroyParameters() {};
  virtual void loadParameters(MixMHParam * param) {};

  virtual ~GKernel() {}

  void infer(uint32_t N);

  Trace * trace;

};

struct MixMHKernel : GKernel
{
  MixMHKernel(Trace * trace, GKernel * gKernel):
    GKernel(trace), gKernel(gKernel) {}

  virtual MixMHIndex * sampleIndex() =0;
  virtual double logDensityOfIndex(MixMHIndex * index) =0;
  virtual MixMHParam * processIndex(MixMHIndex * index) =0;
  
  double propose() override;
  void accept() override { gKernel->accept(); gKernel->destroyParameters(); }
  void reject() override { gKernel->reject(); gKernel->destroyParameters(); }
  
  GKernel* gKernel;

  void destroyChildGKernel() { delete gKernel; }

  /* constructed anew for each proposal */
  MixMHIndex * index;
};
#endif
