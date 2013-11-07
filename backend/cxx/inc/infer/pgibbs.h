#ifndef P_GIBBS_H
#define P_GIBBS_H

#include "infer/gkernel.h"


struct PGibbsParam : MixMHParam 
{ 
  Scaffold * scaffold{nullptr};
  vector<vector<uint32_t> > ancestorIndices;
  vector<vector<OmegaDB*> > omegaDBs;
  vector<double> weights;
  uint32_t P;
  uint32_t T;
};

struct PGibbsIndex : PGibbsParam,MixMHIndex { };


/* This kernel picks a target in proportion to exp(weight),
   accepts by restoring the chosen particle, rejects by
   restoring the source particle. */
struct PGibbsSelectGKernel : GKernel
{
  PGibbsSelectGKernel(Trace * trace): GKernel(trace) {}

  void loadParameters(MixMHParam * param) override;
  void destroyParameters() override;

  double propose() override;
  void accept() override;
  void reject() override;

private:

  /* the Pth index indicates RHO */
  Scaffold * scaffold{nullptr};
  vector<vector<uint32_t> > ancestorIndices;
  vector<vector<OmegaDB*> > omegaDBs;
  vector<double> weights;
  uint32_t P = UINT32_MAX;
  uint32_t T = UINT32_MAX;


  uint32_t chosenIndex = UINT32_MAX;
};


struct PGibbsGKernel : MixMHKernel
{
  PGibbsGKernel(Trace * trace): 
    MixMHKernel(trace, new PGibbsSelectGKernel(trace)) {}

  ~PGibbsGKernel() { delete gKernel; }
  void destroyParameters();
  void loadParameters(MixMHParam * param);

  MixMHIndex * sampleIndex();
  double logDensityOfIndex(MixMHIndex * index);
  MixMHParam * processIndex(MixMHIndex * index);

  Scaffold * scaffold{nullptr};
  Node * pNode{nullptr};
  size_t P = 10;

};

#endif
