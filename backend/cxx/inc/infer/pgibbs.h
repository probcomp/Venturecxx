#ifndef P_GIBBS_H
#define P_GIBBS_H

#include "infer/gkernel.h"

struct PGibbsIndex : MixMHIndex
{ 
  Scaffold * scaffold{nullptr}; 
  vector<vector<uint32_t> > ancestorIndices;
  vector<vector<OmegaDB*> > omegaDBs;
  vector<double> weights;
  uint32_t P;
  uint32_t T;
};

struct PGibbsParam : MixMHParam 
{ 
  PGibbsParam(const GibbsIndex * pindex):
    scaffold(pindex->scaffold),
    ancestorIndices(move(ancestorIndices)),
    omegaDBs(omegaDBs),
    weights(move(weights)),
    P(P),
    T(T) {}

  Scaffold * scaffold{nullptr};
  vector<vector<uint32_t> > ancestorIndices;
  vector<vector<OmegaDB*> > omegaDBs;
  vector<double> weights;
  uint32_t P;
  uint32_t T;

};

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

  Scaffold * scaffold{nullptr};

  vector<vector<uint32_t> > ancestorIndices;
  vector<vector<OmegaDB*> > omegaDBs;
  vector<double> weights;
  uint32_t P;
  uint32_t T;

  uint32_t chosenIndex = -1;
};


struct PGibbsGKernel : MixMHKernel
{
  PGibbsGKernel(Trace * trace): 
    MixMHKernel(trace, new ParticleGKernel(trace)) {}

  ~PGibbsGKernel() { delete gKernel; }
  void destroyParameters();
  void loadParameters(MixMHParam * param);

  MixMHIndex * sampleIndex();
  double logDensityOfIndex(MixMHIndex * index);
  MixMHParam * processIndex(MixMHIndex * index);

  Scaffold * scaffold{nullptr};
  Node * pNode{nullptr};
  size_t P = 2;

  size_t T; // for now, just the number of border nodes
  vector<vector<uint32_t> > ancestorIndices;
  vector<vector<OmegaDB*> > omegaDBs;
  vector<double> weightsRho;
  vector<double> weights;

};

#endif
