#ifndef INFER_H
#define INFER_H

struct Trace;
struct Scaffold;

#include "infer/gkernel.h"
#include "omegadb.h"

struct ScaffoldMHGKernel : GKernel
{
  ScaffoldMHGKernel(Trace * trace): GKernel(trace) {}

  double propose() override;
  void accept() override;
  void reject() override;

  void destroyParameters() override;
  void loadParameters(MixMHParam * param) override;

  Scaffold * scaffold{nullptr};
  OmegaDB * rhoDB{nullptr};
};

/* TODO ScaffoldParam */
struct ScaffoldMHParam : MixMHParam 
{ 
  ScaffoldMHParam(Scaffold * scaffold, Node *pNode): 
    scaffold(scaffold), pNode(pNode) {}

  Scaffold * scaffold; 
  Node * pNode{nullptr}; /* used for enumeration */
};

/* TODO PrincipalNodeIndex */
struct RCIndex : MixMHIndex 
{ 
  RCIndex(Node * pNode): pNode(pNode) {}
  Node * pNode; 
};

struct OutermostMixMH : MixMHKernel
{
  OutermostMixMH(Trace * trace, GKernel * gKernel): MixMHKernel(trace,gKernel) {}
  /* TODO where to put the flag for DeltaKernels? */
  
  MixMHIndex * sampleIndex() override;
  double logDensityOfIndex(MixMHIndex * index) override;
  MixMHParam * processIndex(MixMHIndex * index) override;
};

/* TODO FIXME this recomputes the global scaffold at every step.
   To fix it, have the outer layers delete the parameters instead
   of the inner layers, or use shared pointers. */
struct GlobalScaffoldMixMH : MixMHKernel
{
  GlobalScaffoldMixMH(Trace * trace, GKernel * gKernel): MixMHKernel(trace,gKernel) {}
  
  MixMHIndex * sampleIndex() override;
  double logDensityOfIndex(MixMHIndex * index) override;
  MixMHParam * processIndex(MixMHIndex * index) override;
};


#endif
