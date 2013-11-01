#ifndef INFER_H
#define INFER_H

#include "gkernel.h"
#include "trace.h"
#include "scaffold.h"
#include "omegadb.h"

struct ScaffoldMHGKernel : GKernel
{
  ScaffoldMHGKernel(Trace * trace, Scaffold * scaffold): 
    GKernel(trace), scaffold(scaffold) {}

  double propose() override;
  void accept() override;
  void reject() override;

  Scaffold * scaffold;

  OmegaDB rhoDB;

};

struct ScaffoldMHParam : MixMHParam 
{ 
  ScaffoldMHParam(Scaffold * scaffold): scaffold(scaffold) {}
  Scaffold * scaffold; 
};

struct ScaffoldMHGKernelMaker : GKernelMaker
{
  ScaffoldMHGKernelMaker(Trace * trace): GKernelMaker(trace) {}
  GKernel * constructGKernel(MixMHParam * param) override
    {
      Scaffold * scaffold = dynamic_cast<ScaffoldMHParam *>(param)->scaffold;
      return new ScaffoldMHGKernel(trace,scaffold);
    }
};

struct RCIndex : MixMHIndex 
{ 
  RCIndex(Node * pNode): pNode(pNode) {}
  Node * pNode; 
};

struct OutermostMixMH : MixMHKernel
{
  OutermostMixMH(Trace * trace, GKernelMaker * gKernelMaker): MixMHKernel(trace,gKernelMaker) {}
  /* TODO where to put the flag for DeltaKernels? */
  
  MixMHIndex * sampleIndex() override;
  double logDensityOfIndex(MixMHIndex * index) override;
  MixMHParam * processIndex(MixMHIndex * index) override;
};


#endif
