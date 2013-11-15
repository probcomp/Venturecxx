#include "infer/mh.h"
#include "node.h"
#include "check.h"
#include "flush.h"
#include "debug.h"
#include "trace.h"
#include "scaffold.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>


#include <algorithm>
#include <iostream>

/* ScaffoldMHGKernel */

ScaffoldMHGKernel::ScaffoldMHGKernel(Trace * trace): 
  GKernel(trace), check(trace) {}

void ScaffoldMHGKernel::destroyParameters() { delete scaffold; }
void ScaffoldMHGKernel::loadParameters(MixMHParam * param)
{
  ScaffoldMHParam * sparam = dynamic_cast<ScaffoldMHParam*>(param);
  assert(sparam);
  scaffold = sparam->scaffold;
  delete sparam;
}


double ScaffoldMHGKernel::propose()
{
  assert(scaffold);
  assert(!rhoDB);

  rho = new Particle;
  double rhoWeight = trace->extract(scaffold->border,scaffold,rho);

  check.checkTorus(scaffold);

  xi = new Particle;
  double xiWeight = trace->generate(scaffold->border,scaffold,xi);
  return xiWeight - rhoWeight;
}

void ScaffoldMHGKernel::accept()
{
//  flushDB(rhoDB,false);
  trace->commit(xi);
  delete rho;
  delete xi;
}


void ScaffoldMHGKernel::reject()
{
  trace->commit(rho);
//  flushDB(rhoDB,true);
//  flushDB(xiDB,false);
  delete rho;
  delete xi;
}


/* Outermost MixMH */

MixMHIndex * OutermostMixMH::sampleIndex()
{
  uint32_t index = gsl_rng_uniform_int(trace->rng, trace->numRandomChoices());
  Node * pNode = trace->getRandomChoiceByIndex(index);
  return new RCIndex(pNode);
}

double OutermostMixMH::logDensityOfIndex(MixMHIndex * index)
{
  return -log(trace->numRandomChoices());
}
 
MixMHParam * OutermostMixMH::processIndex(MixMHIndex * index)
{
  Node * pNode = dynamic_cast<RCIndex *>(index)->pNode;

  /* Deleted by deepest gkernel's destroyParameters() */
  Scaffold * scaffold = new Scaffold({pNode});

  /* May expose latent bugs */
  if (gsl_ran_flat(trace->rng,0.0,1.0) < 0.5) { reverse(scaffold->border.begin(),scaffold->border.end()); }

  delete index;

  return new ScaffoldMHParam(scaffold,pNode);
}


MixMHIndex * GlobalScaffoldMixMH::sampleIndex() { return nullptr; }
double GlobalScaffoldMixMH::logDensityOfIndex(MixMHIndex * index) { return 0; }
MixMHParam * GlobalScaffoldMixMH::processIndex(MixMHIndex * index) 
{ 
  vector<Node *> rcs = trace->getRandomChoices();
  set<Node *> allNodes(rcs.begin(),rcs.end());
  return new ScaffoldMHParam(new Scaffold(allNodes),nullptr);
};
