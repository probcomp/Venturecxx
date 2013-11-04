#include "infer/mh.h"
#include "infer/gibbs.h"
#include "flush.h"
#include "utils.h"
#include "trace.h"
#include "scaffold.h"
#include "node.h"
#include "lkernel.h"
#include "value.h"
#include "sp.h"
#include "omegadb.h"
#include "check.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <vector>

#include <cmath>

void GibbsSelectGKernel::loadParameters(MixMHParam * param)
{
  GibbsParam * pparam = dynamic_cast<GibbsParam*>(param);
  assert(pparam);
  scaffold = pparam->scaffold;
  source = pparam->source;
  targets = pparam->targets;
  delete pparam;
}

void GibbsSelectGKernel::destroyParameters()
{
  targets.clear();
  delete scaffold;
}

double GibbsSelectGKernel::propose()
{
  assert(chosenIndex == UINT32_MAX);
  double rhoExpWeight = exp(source.first);

  double totalXiExpWeight = 0;
  vector<double> xiExpWeights;
  for (pair<double,OmegaDB*> p : targets)
  { 
    xiExpWeights.push_back(exp(p.first));
    totalXiExpWeight += xiExpWeights.back();
  }
  normalizeVector(xiExpWeights);

  double u = gsl_ran_flat(trace->rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < xiExpWeights.size(); ++i)
  {
    sum += xiExpWeights[i];
    if (u < sum) { chosenIndex = i; break; }
  }
  
  double weightMinusRho = log(totalXiExpWeight);
  double weightMinusXi = log(rhoExpWeight + totalXiExpWeight - exp(targets[chosenIndex].first));
  assertTorus(trace,scaffold);
  trace->regen(scaffold->border,scaffold,true,targets[chosenIndex].second);
  return weightMinusRho - weightMinusXi;
}

void GibbsSelectGKernel::accept()
{
  assert(chosenIndex != UINT32_MAX);
  flushDB(source.second,false);
  for (size_t i = 0; i < targets.size(); ++i)
  {
    if (i == chosenIndex) { flushDB(targets[i].second,true); }
    else { flushDB(targets[i].second,false); }
  }
  chosenIndex = UINT32_MAX;
}

void GibbsSelectGKernel::reject()
{
  assert(chosenIndex != UINT32_MAX);
  pair<double,OmegaDB *> xiInfo = trace->detach(scaffold->border,scaffold);
  assertTorus(trace,scaffold);
  trace->regen(scaffold->border,scaffold,true,source.second);
  flushDB(source.second,true);
  flushDB(xiInfo.second,true); // subtle! only flush the latents twice (TODO discuss)
  for (size_t i = 0; i < targets.size(); ++i)
  {
    flushDB(targets[i].second,false);
  }
  chosenIndex = UINT32_MAX;
}


/* GibbsGKernel */
void GibbsGKernel::destroyParameters()
{
  /* TODO GC be careful about when te delete scaffold since many layers make
     use of it. */
  scaffold = nullptr;
  pNode = nullptr;
}

void GibbsGKernel::loadParameters(MixMHParam * param)
{
  ScaffoldMHParam * sparam = dynamic_cast<ScaffoldMHParam*>(param);
  assert(sparam);
  scaffold = sparam->scaffold;
  pNode = sparam->pNode;
  delete sparam;
}

MixMHIndex * GibbsGKernel::sampleIndex()
{
  GibbsIndex * pindex = new GibbsIndex;


  pindex->scaffold = scaffold;

  /* Enumerate */
  if (pNode->sp()->canEnumerate(pNode->nodeType))
  {
    vector<VentureValue *> values = pNode->sp()->enumerate(pNode);
    LKernel * lk = new DeterministicLKernel(pNode->getValue(),pNode->sp());
    scaffold->lkernels[pNode] = lk;
    pindex->source = trace->detach(scaffold->border,scaffold);
    assertTorus(trace,scaffold);
    scaffold->lkernels.erase(pNode);
    delete lk;

    for (size_t i = 0; i < values.size(); ++i)
    {
      LKernel * lk = new DeterministicLKernel(values[i],pNode->sp());
      scaffold->lkernels[pNode] = lk;
      trace->regen(scaffold->border,scaffold,false,nullptr);
      pindex->targets.push_back(trace->detach(scaffold->border,scaffold));
      assertTorus(trace,scaffold);
      scaffold->lkernels.erase(pNode);
      delete lk;
    }
  }
  /* Otherwise sample particles */
  else 
  {
    pindex->source = trace->detach(scaffold->border,scaffold);
    assertTorus(trace,scaffold);

    for (size_t p = 0; p < P; ++p)
    {
      trace->regen(scaffold->border,scaffold,false,nullptr);
      pindex->targets.push_back(trace->detach(scaffold->border,scaffold));
      assertTorus(trace,scaffold);
    }
  }
  return pindex;
}

/* This is using the MH_n cancellations */
double GibbsGKernel::logDensityOfIndex(MixMHIndex * index)
{
  return 0;
}


MixMHParam * GibbsGKernel::processIndex(MixMHIndex * index)
{
  GibbsParam * pparam = dynamic_cast<GibbsParam*>(index);
  assert(pparam);
  return pparam;
}




