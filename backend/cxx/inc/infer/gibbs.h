#ifndef GIBBS_H
#define GIBBS_H

#include "infer/gkernel.h"

struct GibbsParam : MixMHParam 
{ 
  Scaffold * scaffold{nullptr}; 
  pair<double,OmegaDB*> source;
  vector<pair<double,OmegaDB*> > targets;
};

struct GibbsIndex : GibbsParam,MixMHIndex { };





/* This kernel picks a target in proportion to exp(weight),
   accepts by restoring the chosen particle, rejects by
   restoring the source particle. */
struct GibbsSelectGKernel : GKernel
{
  GibbsSelectGKernel(Trace * trace): GKernel(trace) {}

  void loadParameters(MixMHParam * param) override;
  void destroyParameters() override;

  double propose() override;
  void accept() override;
  void reject() override;

  Scaffold * scaffold;
  pair<double,OmegaDB*> source;
  vector<pair<double,OmegaDB*> > targets;
  uint32_t chosenIndex = UINT32_MAX;
};


struct GibbsGKernel : MixMHKernel
{
  GibbsGKernel(Trace * trace): 
    MixMHKernel(trace, new GibbsSelectGKernel(trace)) {}

  ~GibbsGKernel() { delete gKernel; }
  void destroyParameters();
  void loadParameters(MixMHParam * param);

  MixMHIndex * sampleIndex();
  double logDensityOfIndex(MixMHIndex * index);
  MixMHParam * processIndex(MixMHIndex * index);

  Scaffold * scaffold{nullptr};
  Node * pNode{nullptr};
  size_t P = 2;

};


#endif
