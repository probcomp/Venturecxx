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

vector<uint32_t> constructAncestorPath(const vector<vector<uint32_t> > & ancestorIndices,
				       uint32_t t, 
				       uint32_t p)
{
  vector<uint32_t> path;
  if (t > 0) 
  { 
    path.push_back(ancestorIndices[t][p]);
  for (int i = t - 1; i >= 1; i--)
  {
    uint32_t ancestor = path.back();
    path.push_back(ancestorIndices[i][ancestor]);
  }
  assert(path.size() == t);
  reverse(path.begin(),path.end());
  }
  return path;

}

void restoreAncestorPath(Trace * trace,
			 Scaffold * scaffold,
			 vector<vector<OmegaDB *> > omegaDBs,
			 vector<uint32_t> path)
{
  for (size_t t = 0; t < path.size(); ++t)
  {
    uint32_t nextParticle = path[t];
    /* TODO We need to divide the border into sub-vectors */
    trace->regen({scaffold->border[t]},scaffold,true,omegaDBs[t][nextParticle]);
  }
}

void discardAncestorPath(Trace * trace,
			 Scaffold * scaffold,
			 uint32_t t)
{
  for (int i = t - 1; i >= 0; i--)
  {
    double weight;
    OmegaDB * detachedDB;
    tie(weight,detachedDB) = trace->detach({scaffold->border[i]},scaffold);
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
  vector<uint32_t> path = constructAncestorPath(ancestorIndices,T-1,chosenIndex);
  path.push_back(chosenIndex);
  assert(path.size() == T);
  restoreAncestorPath(trace,scaffold,omegaDBs,path);
  return weightMinusRho - weightMinusXi;
}


/////////////////////////
//// Accept . Reject ////
/////////////////////////

void PGibbsSelectGKernel::accept()
{
  assert(chosenIndex != UINT32_MAX);
  vector<uint32_t> path = constructAncestorPath(ancestorIndices,T-1,chosenIndex);
  path.push_back(chosenIndex);
  assert(path.size() == T);
  for (size_t t = 0; t < T; ++t)
  { for (size_t p = 0; p < P + 1; ++p)
    { 
      /* Be careful with off-by-one-bugs here */
      bool isActive = (path[t] == p);
      flushDB(omegaDBs[t][p],isActive);
    }
  }

  chosenIndex = UINT32_MAX;
}

void PGibbsSelectGKernel::reject()
{
  assert(chosenIndex != UINT32_MAX);
  discardAncestorPath(trace,scaffold,T);
  assertTorus(trace,scaffold);
  vector<uint32_t> path = constructAncestorPath(ancestorIndices,T-1,P);
  path.push_back(P);
  assert(path.size() == T);
  restoreAncestorPath(trace,scaffold,omegaDBs,path);

  for (size_t t = 0; t < T; ++t)
  { 
    for (size_t p = 0; p < P + 1; ++p)
    { 
      bool isActive = (path[t] == p);
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
}

MixMHIndex * PGibbsGKernel::sampleIndex()
{
  /* TODO allow T to be customized by splitting the border into segments. */
  uint32_t T = scaffold->border.size();
  
  vector<vector<uint32_t> > ancestorIndices(T);
  vector<vector<OmegaDB*> > omegaDBs(T);
  for (size_t t = 0; t < T; t++) 
  { 
    ancestorIndices[t].resize(P+1); 
    omegaDBs[t].resize(P+1);
  }
  vector<double> weightsRho(T);
  vector<double> weights(P+1);

  PGibbsIndex * pindex = new PGibbsIndex;
  pindex->P = P;
  pindex->T = T;

  pindex->scaffold = scaffold;

  for (int t = T-1; t >= 0; --t)
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
      vector<double> expWeights;
      for (size_t i = 0; i < weights.size(); ++i) { expWeights.push_back(exp(weights[i])); }
      ancestorIndices[t][p] = sampleCategorical(expWeights,trace->rng);
      vector<uint32_t> path = constructAncestorPath(ancestorIndices,t,p);
      restoreAncestorPath(trace,scaffold,omegaDBs,path);
      trace->regen({scaffold->border[t]},scaffold,false,nullptr);
      tie(newWeights[p],omegaDBs[t][p]) = trace->detach({scaffold->border[t]},scaffold);
      discardAncestorPath(trace,scaffold,t);
      assertTorus(trace,scaffold);
    }
    weights = newWeights;
  }

  /* Really? */
  pindex->ancestorIndices = ancestorIndices;
  pindex->omegaDBs = omegaDBs;
  pindex->weights = weights;
  
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


