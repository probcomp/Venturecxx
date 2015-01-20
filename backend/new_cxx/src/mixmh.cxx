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
using std::flush;

void mixMH(ConcreteTrace * trace,
	   shared_ptr<ScaffoldIndexer> indexer,
	   shared_ptr<GKernel> gKernel)
{
  shared_ptr<Scaffold> index = indexer->sampleIndex(trace);


  double rhoMix = indexer->logDensityOfIndex(trace,index);

  pair<Trace*,double> p = gKernel->propose(trace,index);
  double xiMix = indexer->logDensityOfIndex(p.first,index);

  double alpha = xiMix + p.second - rhoMix;
  double logU = log(gsl_ran_flat(trace->getRNG(),0.0,1.0));

  
  if (logU < alpha) {
    // cout << ".";
    gKernel->accept();
  }
  else
  {
    // cout << "!";
    gKernel->reject();
  }

}
