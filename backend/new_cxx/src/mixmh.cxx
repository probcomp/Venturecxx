#include "concrete_trace.h"
#include "scaffold.h"
#include "indexer.h"
#include "gkernel.h"
#include "mixmh.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <cmath>

#include <iostream>
using std::cout;
using std::endl;

void mixMH(ConcreteTrace * trace,
	   shared_ptr<ScaffoldIndexer> indexer,
	   shared_ptr<GKernel> gKernel)
{
  shared_ptr<Scaffold> index = indexer->sampleIndex(trace);

//  cout << "Scaffold: " << index->showSizes() << endl;

  double rhoMix = indexer->logDensityOfIndex(trace,index);

  pair<Trace*,double> p = gKernel->propose(trace,index);
  double xiMix = indexer->logDensityOfIndex(p.first,index);

  double alpha = xiMix + p.second - rhoMix;
  double logU = log(gsl_ran_flat(trace->rng,0.0,1.0));

//  cout << "alpha: " << alpha << endl;
  
  if (logU < alpha) { gKernel->accept(); }
  else { gKernel->reject(); }

}
