#include "infer.h"
#include "check.h"
#include "flush.h"

#include <iostream>

/* ScaffoldMHGKernel */

double ScaffoldMHGKernel::propose()
{
  std::pair<double, OmegaDB> rhoInfo = trace->detach(scaffold->border,scaffold);

  /* TODO OPT these should be moves. */
  double detachWeight = rhoInfo.first;
  rhoDB = rhoInfo.second;

  assertTorus(trace,scaffold);
  double regenWeight = trace->regen(scaffold->border,scaffold,false,rhoDB);
  return regenWeight - detachWeight;
}

void ScaffoldMHGKernel::accept()
{
  flushDB(rhoDB);
}
 
void ScaffoldMHGKernel::reject()
{
  std::pair<double, OmegaDB> xiInfo = trace->detach(scaffold->border,scaffold);
  OmegaDB & xiDB = xiInfo.second;

  assertTorus(trace,scaffold);

  trace->regen(scaffold->border,scaffold,true,rhoDB);
  flushDB(rhoDB);
  flushDB(xiDB);
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
  Scaffold * scaffold = new Scaffold({pNode});
  return new ScaffoldMHParam(scaffold);
}

