#include "value.h"
#include "node.h"
#include "makelazyhmm.h"
#include "omegadb.h"
#include "value.h"

#include <cmath>
#include <algorithm>

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

VectorXd vvToEigenVector(VentureValue * value);
MatrixXd vvToEigenMatrix(VentureValue * value);
uint32_t indexOfOne(const VectorXd & v);
VectorXd sampleVectorXd(const VectorXd & v,gsl_rng * rng);
uint32_t sampleVector(const VectorXd & v,gsl_rng * rng);
VectorXd normalizedVectorXd(VectorXd & v);

/* AAA LKernel */

VentureValue * MakeLazyHMMAAAKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB, gsl_rng * rng)
{
  VectorXd p0 = vvToEigenVector(appNode->operandNodes[0]->getValue());
  MatrixXd T =  vvToEigenMatrix(appNode->operandNodes[1]->getValue());
  MatrixXd O =  vvToEigenMatrix(appNode->operandNodes[2]->getValue());

  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(appNode->madeSPAux);

  if (aux->os.empty()) { return new VentureSP(new LazyHMMSP(p0,T,O)); }

  uint32_t maxObservation = (*(max_element(aux->os.begin(),aux->os.end()))).first;
  vector<VectorXd> fs{p0};

  /* Forwards filtering */
  for (size_t i = 1; i <= maxObservation; ++i)
  {
    VectorXd f = T * fs[i-1];
    if (aux->os.count(i))
    {
      assert(aux->os[i].size() == 1);
      for (uint32_t j : aux->os[i])
      {
	f = O.row(j).asDiagonal() * f;
      }
    }
    fs.push_back(normalizedVectorXd(f));
  }

  /* Backwards sampling */
  aux->xs.resize(maxObservation + 1);

  aux->xs[maxObservation] = sampleVectorXd(fs[maxObservation],rng);
  for (int i = maxObservation-1; i >= 0; --i)
  {
    size_t rowIndex = indexOfOne(aux->xs[i+1]);
    MatrixXd T_i = T.row(rowIndex).asDiagonal();
    VectorXd gamma = T_i * fs[i];
    aux->xs[i] = sampleVectorXd(normalizedVectorXd(gamma),rng);
  }

  return new VentureSP(new LazyHMMSP(p0,T,O));
}

/* MakeLazyHMMSP */

VentureValue * MakeLazyHMMSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  return 
    new VentureSP(new LazyHMMSP(vvToEigenVector(node->operandNodes[0]->getValue()),
				vvToEigenMatrix(node->operandNodes[1]->getValue()),
				vvToEigenMatrix(node->operandNodes[2]->getValue())));
}

pair<double,LatentDB *> MakeLazyHMMSP::detachAllLatents(SPAux * spaux) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux*>(spaux);
  LazyHMMLatentDBAll * latents = new LazyHMMLatentDBAll;
  latents->xs.swap(aux->xs);
  return {0,latents};
}
 
void MakeLazyHMMSP::restoreAllLatents(SPAux * spaux, LatentDB * latentDB)
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux*>(spaux);
  LazyHMMLatentDBAll * latents = new LazyHMMLatentDBAll;
  latents->xs.swap(aux->xs);
}

/* LazyHMMSP */

SPAux * LazyHMMSP::constructSPAux() const { return new LazyHMMSPAux; }
void LazyHMMSP::destroySPAux(SPAux * spaux) { delete spaux; }

void LazyHMMSP::incorporateOutput(VentureValue * value, Node * node) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux*>(node->spaux());
  VentureAtom * vout = dynamic_cast<VentureAtom *>(value);
  VentureNumber * vin = dynamic_cast<VentureNumber *>(node->operandNodes[0]->getValue());

  assert(aux);
  assert(vout);
  assert(vin);

  assert(vout->n < 100); // TODO DEBUG

  /* Register observation */
  aux->os[vin->getInt()].push_back(vout->n);
}

void LazyHMMSP::removeOutput(VentureValue * value, Node * node) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux*>(node->spaux());
  VentureAtom * vout = dynamic_cast<VentureAtom *>(value);
  VentureNumber * vin = dynamic_cast<VentureNumber *>(node->operandNodes[0]->getValue());

  assert(aux);
  assert(vout);
  assert(vin);

  vector<uint32_t> & iObs = aux->os[vin->getInt()];
  size_t oldSize = iObs.size();

  /* Remove observation. */
  iObs.erase(find(iObs.begin(),iObs.end(),vout->n));
  assert(oldSize == iObs.size() + 1);
  if (iObs.empty()) { aux->os.erase(vin->getInt()); }
}


double LazyHMMSP::simulateLatents(SPAux * spaux,
				  HSR * hsr,
				  bool shouldRestore,
				  LatentDB * latentDB,
				  gsl_rng * rng) const
{
  /* TODO CURRENT SPOT */
  /* if should restore, restore, otherwise do not assert latentDB */
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(spaux);
  HMM_HSR * request = dynamic_cast<HMM_HSR *>(hsr);
  LazyHMMLatentDBSome * latents = nullptr;
  if (latentDB)
  { 
    latents = dynamic_cast<LazyHMMLatentDBSome *>(latentDB);
    assert(latents);
  }
  
  assert(aux);
  assert(request);

  /* No matter what the request is, we must sample the first latent if
     we have not already done so. */
  if (aux->xs.empty()) { aux->xs.push_back(sampleVectorXd(p0,rng)); }

  if (aux->xs.size() <= request->index)
  {
    for (size_t i = aux->xs.size(); i <= request->index; ++i)
    {
      VectorXd sample;
      if (shouldRestore) { sample = latents->xs[i]; }
      else { sample = sampleVectorXd(T * aux->xs.back(),rng); }
      aux->xs.push_back(sample);
    }
  }
  return 0;
}

double LazyHMMSP::detachLatents(SPAux * spaux,
				HSR * hsr,
				LatentDB * latentDB) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(spaux);
  HMM_HSR * request = dynamic_cast<HMM_HSR *>(hsr);
  LazyHMMLatentDBSome * latents = dynamic_cast<LazyHMMLatentDBSome *>(latentDB);

  assert(aux);
  assert(request);
  assert(latents);

  if (aux->xs.size() == request->index + 1 && 
      !aux->os.count(request->index))
  {
    if (aux->os.empty()) 
    { 
      for (size_t i = 0; i < aux->xs.size(); ++i)
      { latents->xs[i] = aux->xs[i]; }
      aux->xs.clear();
    }
    else
    {
      uint32_t maxObservation = (*(max_element(aux->os.begin(),aux->os.end()))).first;
      for (size_t i = aux->xs.size()-1; i > maxObservation; --i)
      {
	latents->xs[i] = aux->xs.back();
	aux->xs.pop_back();
      }
      assert(aux->xs.size() == maxObservation + 1);
    }
  }
  return 0;
}


VentureValue * LazyHMMSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(node->spaux());
  VentureNumber * vint = dynamic_cast<VentureNumber*>(node->operandNodes[0]->getValue());
  assert(aux);
  assert(vint);

  return new VentureAtom(sampleVector(O * aux->xs[vint->getInt()],rng));
}

double LazyHMMSP::logDensityOutput(VentureValue * value, Node * node) const
{
  VentureAtom * vout = dynamic_cast<VentureAtom*>(value);
  VentureNumber * vin = dynamic_cast<VentureNumber*>(node->operandNodes[0]->getValue());
  assert(vout);
  assert(vin);

  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(node->spaux());

  assert(aux->xs.size() > vin->getInt());
  VectorXd dist = O * aux->xs[vin->getInt()];
  return log(dist[vout->n]);
}

VentureValue * LazyHMMSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  VentureNumber * vin = dynamic_cast<VentureNumber*>(node->operandNodes[0]->getValue());
  assert(vin);
  vector<HSR *> hsrs;
  return new VentureRequest({new HMM_HSR(vin->getInt())});
}

/* Helpers */

VectorXd vvToEigenVector(VentureValue * value)
{
  VentureVector * vvec = dynamic_cast<VentureVector*>(value);
  assert(vvec);

  size_t len = vvec->xs.size();
  VectorXd v(len);

  for (size_t i = 0; i < len; ++i)
  {
    VentureNumber * vdouble = dynamic_cast<VentureNumber*>(vvec->xs[i]);
    assert(vdouble);
    v(i) = vdouble->x;
  }
  return v;
}

MatrixXd vvToEigenMatrix(VentureValue * value)
{
  uint32_t rows, cols;

  VentureVector * allRows = dynamic_cast<VentureVector*>(value);
  assert(allRows);
  rows = allRows->xs.size();
  assert(rows > 0);

  VentureVector * vrow0 = dynamic_cast<VentureVector*>(allRows->xs[0]);
  assert(vrow0);
  cols = vrow0->xs.size();
  assert(cols > 0);

  MatrixXd M(rows,cols);

  for (size_t i = 0; i < rows; ++i)
  {
    VentureVector * vrow = dynamic_cast<VentureVector*>(allRows->xs[i]);
    assert(vrow);
    assert(cols == vrow->xs.size());
    
    for (size_t j = 0; j < cols; ++j)
    {
      VentureNumber * vdouble = dynamic_cast<VentureNumber*>(vrow->xs[j]);
      assert(vdouble);
      M(i,j) = vdouble->x;
    }
  }
  return M;
}

uint32_t indexOfOne(const VectorXd & v)
{
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i)
  {
    if (v[i] == 1) { return i; }
    else { assert(v[i] == 0); }
  }
  assert(false);
  return -1;
}

VectorXd sampleVectorXd(const VectorXd & v,gsl_rng * rng)
{
  VectorXd sample(v.size());
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i) { sample[i] = 0; }

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < len; ++i)
  {
    sum += v[i];
    if (u < sum) 
    { 
      sample[i] = 1;
      return sample;
    }
  }
  assert(false);
  return sample;
}

uint32_t sampleVector(const VectorXd & v,gsl_rng * rng)
{
  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i)
  {
    sum += v[i];
    if (u < sum) { return i; }
  }
  assert(false);
  return -1;
}

VectorXd normalizedVectorXd(VectorXd & v)
{
  
  size_t len = v.size();
  double sum = 0;
  for (size_t i = 0; i < len; ++i) { sum += v[i]; }

  VectorXd newVector(len);
  for (size_t i = 0; i < len; ++i) { newVector[i] = v[i] / sum; }
  return newVector;
}
