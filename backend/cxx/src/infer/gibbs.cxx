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
  check.checkTorus(scaffold);

  trace->regen(scaffold->border,scaffold,true,targets[chosenIndex].second,nullptr);
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
  check.checkTorus(scaffold);
  trace->regen(scaffold->border,scaffold,true,source.second,nullptr);
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

  bool canEnumerate = false;

  /* Enumerate */
  if (pNode->sp()->canEnumerate(pNode->nodeType))
  {
    vector<VentureValue *> values = pNode->sp()->enumerate(trace->getArgs(pNode));
    const VentureValue * oldValue = trace->getValue(pNode);
    if (values.size() > 1)
    {
      canEnumerate = true;
      LKernel * lk = new DeterministicLKernel(oldValue,trace->getSP(pNode));
      scaffold->lkernels[pNode] = lk;
      pindex->source = trace->detach(scaffold->border,scaffold);
      check.checkTorus(scaffold);
      scaffold->lkernels.erase(pNode);
      delete lk;

      for (size_t i = 0; i < values.size(); ++i)
      {
	const VentureValue * newValue = values[i];
	if (newValue->equals(oldValue)) { continue; }
	LKernel * lk = new DeterministicLKernel(values[i],pNode->sp());
	scaffold->lkernels[pNode] = lk;
	trace->regen(scaffold->border,scaffold,false,nullptr,nullptr);
	pindex->targets.push_back(trace->detach(scaffold->border,scaffold));
	check.checkTorus(scaffold);
	scaffold->lkernels.erase(pNode);
	delete lk;
      }
    }
  }

  /* Otherwise sample particles */
  if (!canEnumerate)
  {
    pindex->source = trace->detach(scaffold->border,scaffold);
    check.checkTorus(scaffold);

    for (size_t p = 0; p < P; ++p)
    {
      trace->regen(scaffold->border,scaffold,false,nullptr,nullptr);
      pindex->targets.push_back(trace->detach(scaffold->border,scaffold));
      check.checkTorus(scaffold);
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




