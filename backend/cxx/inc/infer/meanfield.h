#ifndef MEAN_FIELD_H
#define MEAN_FIELD_H

#include "infer/gkernel.h"
#include "infer/mh.h"

struct MeanFieldGKernel : GKernel
{
  MeanFieldIProjectorGKernel(Trace * trace): GKernel(trace) {}

  double propose() override;
  void accept() override;
  void reject() override;

  void destroyParameters() override;

  /* Takes a scaffold and a pNode and initializes a variational distribution by
     stochastic gradient descent. */
  void loadParameters(MixMHParam * param) override;

  Scaffold * scaffold{nullptr};
  OmegaDB * rhoDB{nullptr};

  void registerVariationialLKernels();
  
  /* Computed during loadParameters */
  map<Node *, VariationalLKernel *> variationalLKernels;
  
};




#endif
