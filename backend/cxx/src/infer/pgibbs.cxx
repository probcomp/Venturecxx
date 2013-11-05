#include "infer/mh.h"
#include "infer/pgibbs.h"
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


////////////////////////////////
///// PGibbsSelectGKernel //////
////////////////////////////////


/////////////////////////
/////// Helpers /////////
/////////////////////////

stack<uint32_t> PGibbsSelectGKernel::constructAncestorPath(uint32_t t, uint32_t p)
{
  stack<uint32_t> path;
  if (t > 0) { path.push_back(ancestorIndices[t][n]); }
  for (int i = t - 1; i >= 0; i--)
  {
    uint32_t ancestor = path.back();
    path.push_back(ancestorIndices[i][ancestor]);
  }
  assert(path.size() == t);
  return path;
}

void PGibbsSelectGKernel::restoreAncestorPath(stack<uint32_t> path)
{
  int t = 0;
  while (!path.empty())
  {
    uint32_t nextParticle = path.back;
    /* TODO We need to divide the border into sub-vectors */
    trace->regen({scafold->border[t]},scaffold,true,omegaDBs[t][nextParticle]);
    path.pop_back();
    t++;
  }
}

void PGibbsSelectGKernel::discardAncestorPath(uint32_t t)
{
  for (int i = t - 1; i >= 0; i--)
  {
    double weight;
    OmegaDB * detachedDB;
    tie(weight,detachedDB) = detach({scaffold->border[i]},scaffold);
    flushDB(detachedDB,true);
  }
}


///////////////////////////////////
/////// Setup . Teardown //////////
///////////////////////////////////

void PGibbsSelectGKernel::loadParameters(MixMHParam * param)
{
  PGibbsParam * pparam = dynamic_cast<PGibbsParam*>(param);
  assert(pparam);
  scaffold = pparam->scaffold;
  ancestorIndices = pparam->ancestorIndices;
  omegaDBs = pparam->omegaDBs;
  weights = pparam->weights;
  P = pparam->P;
  T = pparam->T;
  delete pparam;
}


void PGibbsSelectGKernel::destroyParameters()
{
  delete scaffold;
  omegaDBs.clear();
  ancestorIndices.clear();
  weights.clear();
  P = UINT32_MAX;
  T = UINT32_MAX;
}

//////////////////////////////
///////// Propose ////////////
//////////////////////////////

double PGibbsSelectGKernel::propose()
{
  assert(chosenIndex == UINT32_MAX);
  double rhoExpWeight = exp(weights[P]);

  double totalXiExpWeight = 0;
  vector<double> xiExpWeights;
  for (size_t i = 0; i < weights.size() - 1; ++i)
  { 
    xiExpWeights.push_back(exp(weights[i]));
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
  double weightMinusXi = log(rhoExpWeight + totalXiExpWeight - exp(weights[chosenIndex]));
  assertTorus(trace,scaffold);
  restoreAncestorPath(constructAncestorPath(T, chosenIndex));
  return weightMinusRho - weightMinusXi;
}


/////////////////////////
//// Accept . Reject ////
/////////////////////////

void PGibbsSelectGKernel::accept()
{
  assert(chosenIndex != -1);
  vector<uint32_t> path = constructAncestorPath(T,chosenIndex);

  for (size_t t = 0; t < T; ++t)
  { for (size_t p = 0; p < P + 1; ++p)
    { 
      /* Be careful with off-by-one-bugs here */
      bool isActive = (path[t] == p);
      flushDB(omegaDBs[t][p],isActive);
    }
  }

  chosenIndex = -1;
}

void PGibbsSelectGKernel::reject()
{
  assert(chosenIndex != -1);
  discardAncestorPath(T);
  assertTorus(trace,scaffold);
  vector<uint32_t> path = constructAncestorPath(ancestorIndices,T,P);
  restoreAncestorPath(path);

  for (size_t t = 0; t < T; ++t)
  { 
    for (size_t p = 0; p < P + 1; ++p)
    { 
      isActive = (path[t] == p);
      flushDB(omegaDBs[t][p],isActive);
    }
  }
  chosenIndex = -1;
}


/////////////////////////
///// PGibbsGKernel /////
/////////////////////////

void PGibbsGKernel::destroyParameters()
{
  scaffold = nullptr;
  pNode = nullptr;
}

void PGibbsGKernel::loadParameters(MixMHParam * param)
{
  ScaffoldMHParam * sparam = dynamic_cast<ScaffoldMHParam*>(param);
  assert(sparam);
  scaffold = sparam->scaffold;
  pNode = sparam->pNode;
  delete sparam;

  /* TODO allow T to be customized by splitting the border into segments. */
  T = scaffold->border.size();
  ancestorIndices.resize(T);
  omegaDBs.resize(T);
  for (size_t t = 0; t < T; t++) 
  { 
    ancestorIndices[t].resize(P+1); 
    omegaDBs[t].resize(P+1);
  }
  weightsRho.resize(T);
  weights.resize(P+1);
}

MixMHIndex * PGibbsGKernel::sampleIndex()
{
  ParticleIndex * pindex = new ParticleIndex;
  pindex->P = P;
  pindex->T = T;

  pindex->scaffold = scaffold;
  for (int t = T-1; t >= 0; ++t)
  {
    tie(weightsRho[t],omegaDBs[t][P]) = trace->detach({scaffold->border[t]},scaffold);
  }
  assertTorus(trace,scaffold);

  /* Simulate and calculate initial weights */
  for (size_t p = 0; p < P; ++p)
  {
    trace->regen({scaffold->border[0]},scaffold,false,nullptr);
    tie(weights[p],omegaDBs[0][p]) = trace->detach({scaffold->border[0]},scaffold);
    assertTorus(trace,scaffold);
  }

  /* For every time step, */
  for (size_t t = 1; t < T; ++t)
  {
    vector<double> newWeights(P+1);
    /* For every particle, */
    for (size_t p = 0; p < P; ++p)
    {
      weights[P] = weightsRho[t-1];
      ancestorIndices[t][n] = sampleCategorical(weights,trace->rng);
      vector<uint32_t> path = constructAncestorPath(t,p);
      restoreAncestorPath(path);
      trace->regen(scaffold->border[t],scaffold,false,nullptr);
      tie(newWeights[p],omegaDBs[t][p]) = trace->detach({scaffold->border[t]},scaffold);
      discardAncestorPath(t);
      assertTorus(trace,scaffold);
    }
    weights = newWeights;
  }

  /* Really? */
  pindex->ancestorIndices = move(ancestorIndices);
  pindex->omegaDBs = move(omegaDBs);
  pindex->weights = move(weights);
  
  return pindex;
}

/* This is using the MH_n cancellations */
double PGibbsGKernel::logDensityOfIndex(MixMHIndex * index)
{
  return 0;
}

MixMHParam * PGibbsGKernel::processIndex(MixMHIndex * index)
{
  PGibbsParam * pparam = dynamic_cast<PGibbsParam*>(index);
  assert(pparam);
  return pparam;
}


