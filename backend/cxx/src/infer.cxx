#include "infer.h"
#include "check.h"
#include "flush.h"
#include "debug.h"
#include "trace.h"
#include "scaffold.h"

#include <iostream>

/* ScaffoldMHGKernel */

double ScaffoldMHGKernel::propose()
{
  LPRINT("propose","!");
  pair<double, OmegaDB> rhoInfo = trace->detach(scaffold->border,*scaffold);

  /* TODO OPT these should be moves. */
  double detachWeight = rhoInfo.first;
  rhoDB = rhoInfo.second;

  assertTorus(*trace,*scaffold);
  double regenWeight = trace->regen(scaffold->border,*scaffold,false,rhoDB);
  return regenWeight - detachWeight;
}

void ScaffoldMHGKernel::accept()
{
  LPRINT("accept","!");
  flushDB(rhoDB);
}


void ScaffoldMHGKernel::reject()
{
  LPRINT("reject","!"); 
  pair<double, OmegaDB> xiInfo = trace->detach(scaffold->border,*scaffold);
  OmegaDB & xiDB = xiInfo.second;
  flushDB(xiDB);
  assertTorus(*trace,*scaffold);
  trace->regen(scaffold->border,*scaffold,true,rhoDB);
}


ScaffoldMHParam::~ScaffoldMHParam() { delete scaffold; }

/* Outermost MixMH */

MixMHIndex * OutermostMixMH::sampleIndex()
{
  uint32_t index = gsl_rng_uniform_int(trace->rng, trace->numRandomChoices());
  Node * pNode = trace->getRandomChoiceByIndex(index);
  /* GC freed in MixMHKernel.reset() */
  return new RCIndex(pNode);
}

double OutermostMixMH::logDensityOfIndex(MixMHIndex * index)
{
  return -log(trace->numRandomChoices());
}
 
MixMHParam * OutermostMixMH::processIndex(MixMHIndex * index)
{
  Node * pNode = dynamic_cast<RCIndex *>(index)->pNode;

  /* GC freed in ScaffoldMHParam destructor. */  
  Scaffold * scaffold = new Scaffold({pNode});

  /* GC freed in MixMHKernel.reset() */
  return new ScaffoldMHParam(scaffold);
}

