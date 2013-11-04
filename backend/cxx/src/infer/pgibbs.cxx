#include "pgibbs.h"

/////////////////////////
/////// Helpers /////////
/////////////////////////

vector<uint32_t> constructAncestorPath(const vector<vector<uint32_t> > & ancestorIndices,
				       uint32_t t,
				       uint32_t p);

/* Weak flushes the redundant OmegaDBs as it detaches. */
void discardAncestorPath(Trace * trace,
			 Scaffold *scaffold, 
			 uint32_t t);

void restoreAncestorPath(Trace * trace,
			 Scaffold * scaffold,
			 const vector<vector<OmegaDB> > & omegaDBs,
			 uint32_t t,
			 vector<uint32_t> path);


/////////////////////////
// PGibbsSelectGKernel //
/////////////////////////

void PGibbsSelectGKernel::loadParameters(MixMHParam * param)
{
  PGibbsParam * pparam = dynamic_cast<PGibbsParam*>(param);
  assert(pparam);
  scaffold = pparam->scaffold;
  ancestorIndices = move(pparam->ancestorIndices);
  omegaDBs =  move(pparam->omegaDBs);
  weights = move(pparam->weights);
  P = pparam->P;
  T = pparam->T;

  delete pparam;
}

void PGibbsSelectGKernel::destroyParameters()
{
  delete scaffold;
  ancestorIndices.clear();
  omegaDBs.clear();
  weights.clear();
  P = -1;
  T = -1;
}

double PGibbsSelectGKernel::propose()
{
  assert(chosenIndex == -1);
  double rhoExpWeight = exp(weights[P]);

  double totalXiExpWeights = 0;
  vector<double> xiExpWeights;
  for (int p = 0; i < P; ++i) 
  { 
    xiExpWeights.push_back(exp(weights[p]));
    totalXiExpWeights += xiExpWeights.back(); 
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

  vector<uint32_t> path = constructAncestorPath(ancestorIndices,T,chosenIndex);
  restoreAncestorPath(trace,scaffold,omegaDBs,T,path);

  return weightMinusRho - weightMinusXi;
}

void PGibbsSelectGKernel::accept()
{
  assert(chosenIndex != -1);
  vector<uint32_t> path = constructAncestorPath(ancestorIndices,T,chosenIndex);

  for (size_t t = 0; t < T; ++t)
  { for (size_t p = 0; p < P + 1; ++p)
    { 
      /* Be careful with off-by-one-bugs here */
      if (path[t] == p)) { flushDBWeak(omegaDBs[t][p]); }
      else { flushDB(omegaDBs[t][p]); }
    }
  }

  chosenIndex = -1;
}

void PGibbsSelectGKernel::reject()
{
  assert(chosenIndex != -1);
  discardAncestorPath(trace,scaffold,T);
  assertTorus(*trace,*scaffold);
  vector<uint32_t> path = constructAncestorPath(ancestorIndices,T,P);
  restoreAncestorPath(trace,scaffold,omegaDBs,T,path);

  for (size_t t = 0; t < T; ++t)
  { for (size_t p = 0; p < P + 1; ++p)
    { 
      if (path[t] == p)) { flushDBWeak(omegaDBs[t][p]); }
      else { flushDB(omegaDBs[t][p]); }
    }
  }

  chosenIndex = -1;
}


/////////////////

/////////////////////////
///// PGibbsGKernel /////
/////////////////////////

void PGibbsGKernel::destroyParameters()
{
  delete scaffold;
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
    tie(weightsRho[t],omegaDBs[t][P]) = trace->detach(scaffold->border,*scaffold);
  }
  assertTorus(*trace,*scaffold);

  /* Simulate and calculate initial weights */
  for (size_t p = 0; p < P; ++p)
  {
    OmegaDB nullDB;
    trace->regen(scaffold->border,*scaffold,false,nullDB);
    tie(weights[p],omegaDBs[0][p]) = trace->detach(scaffold->border,*scaffold);
    assertTorus(*trace,*scaffold);
  }

  /* For every time step, */
  for (size_t t = 1; t < T; ++t)
  {
    vector<double> newWeights(P+1);
    /* For every particle, */
    for (size_t p = 0; p < P; ++p)
    {
      weights[P] = weightsRho[t-1];
      /* move to utils */
      ancestorIndices[t][n] = sampleCategorical(weights,trace->rng);
      vector<uint32_t> path = constructAncestorPath(ancestorIndices,t,p);
      restoreAncestorPath(trace,scaffold,omegaDBs,t,path);
      trace->regen(scaffold->border[t],scaffold,false,OmegaDB());
      tie(newWeights[p],omegaDBs[t][p]) = trace->detach(scaffold->border[t],scaffold);
      discardAncestorPath(trace,scaffold,t);
      assertTorus(*trace,*scaffold);
    }
    weights = newWeights;
  }

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
  ParticleIndex * pindex = dynamic_cast<ParticleIndex*>(index);
  assert(pindex);
  return new ParticleParam(pindex);
}



//////////////////////////////
/// Helper Implementations ///
//////////////////////////////

/////////////////////////
/////// Helpers /////////
/////////////////////////

vector<uint32_t> constructAncestorPath(const vector<vector<uint32_t> > & ancestorIndices,
				       uint32_t t,
				       uint32_t p)
{
  assert(false);
  return {};
}
void discardAncestorPath(Trace * trace,
			Scaffold *scaffold, 
			uint32_t t)
{
  assert(false);
}

void restoreAncestorPath(Trace * trace,
			 Scaffold * scaffold,
			 const vector<vector<OmegaDB> > & omegaDBs,
			 uint32_t t,
			 vector<uint32_t> path)
{
  assert(false);
}
