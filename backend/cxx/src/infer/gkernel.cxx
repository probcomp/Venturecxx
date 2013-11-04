#include "infer/gkernel.h"
#include "node.h"
#include <iostream>

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include "trace.h"
#include <cmath>

void GKernel::infer(uint32_t N)
{
  for (uint32_t i = 0; i < N; ++i)
  {
    double alpha = propose();
    double logU = log(gsl_ran_flat(trace->rng,0.0,1.0));
    if (logU < alpha) { accept(); }
    else { reject(); }
  }
}


double MixMHKernel::propose()
{
  index = sampleIndex();
  double ldRho = logDensityOfIndex(index);
  /* ProcessIndex is responsible for freeing the index. */
  /* LoadParameters is responsible for freeing the param. */
  gKernel->loadParameters(processIndex(index));
  double alpha = gKernel->propose();
  double ldXi = logDensityOfIndex(index);

  return alpha + ldXi - ldRho;
}
 

