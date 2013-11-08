#include "infer/mh.h"
#include "node.h"
#include "check.h"
#include "flush.h"
#include "debug.h"
#include "trace.h"
#include "scaffold.h"

#include <iostream>

/* ScaffoldMHGKernel */

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
  LPRINT("propose","!");
  assert(scaffold);
  assert(!rhoDB);

  pair<double, OmegaDB*> rhoInfo = trace->detach(scaffold->border,scaffold);

  double detachWeight = rhoInfo.first;
  rhoDB = rhoInfo.second;

  assertTorus(trace,scaffold);
  double regenWeight = trace->regen(scaffold->border,scaffold,false,rhoDB,nullptr);
  return regenWeight - detachWeight;
}

void ScaffoldMHGKernel::accept()
{
  LPRINT("accept","!");
  flushDB(rhoDB,false);
  rhoDB = nullptr;
}


void ScaffoldMHGKernel::reject()
{
  LPRINT("reject","!"); 
  pair<double, OmegaDB *> xiInfo = trace->detach(scaffold->border,scaffold);
  OmegaDB * xiDB = xiInfo.second;
  assertTorus(trace,scaffold);
  trace->regen(scaffold->border,scaffold,true,rhoDB,nullptr);
  flushDB(rhoDB,true);
  flushDB(xiDB,false);
  rhoDB = nullptr;

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
