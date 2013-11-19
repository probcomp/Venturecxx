#include "value.h"
#include "node.h"
#include "makelazyhmm.h"
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

SPAux * LazyHMMSPAux::clone() const { return new LazyHMMSPAux(*this); }

/* AAA LKernel */
VentureValue * MakeLazyHMMAAAKernel::simulate(VentureValue * oldVal, const Args & args, gsl_rng * rng)
{
  VectorXd p0 = vvToEigenVector(args.operands[0]);
  MatrixXd T =  vvToEigenMatrix(args.operands[1]);
  MatrixXd O =  vvToEigenMatrix(args.operands[2]);

  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(args.madeSPAux);

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

VentureValue * MakeLazyHMMSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  return 
    new VentureSP(new LazyHMMSP(vvToEigenVector(args.operands[0]),
				vvToEigenMatrix(args.operands[1]),
				vvToEigenMatrix(args.operands[2])));
}

double MakeLazyHMMSP::detachAllLatents(SPAux * spaux) const
{
  latents->xs.clear();
  return 0;
}
 

/* LazyHMMSP */

SPAux * LazyHMMSP::constructSPAux() const { return new LazyHMMSPAux; }
void LazyHMMSP::destroySPAux(SPAux * spaux) { delete spaux; }

void LazyHMMSP::incorporateOutput(VentureValue * value, const Args & args) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux*>(node->spaux());
  VentureAtom * vout = dynamic_cast<VentureAtom *>(value);
  VentureNumber * vin = dynamic_cast<VentureNumber *>(args.operands[0]);

  assert(aux);
  assert(vout);
  assert(vin);

  assert(vout->n < 100); // TODO DEBUG

  /* Register observation */
  aux->os[vin->getInt()].push_back(vout->n);
}

void LazyHMMSP::removeOutput(VentureValue * value, const Args & args) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux*>(node->spaux());
  VentureAtom * vout = dynamic_cast<VentureAtom *>(value);
  VentureNumber * vin = dynamic_cast<VentureNumber *>(args.operands[0]);

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
				  gsl_rng * rng) const
{
  /* TODO CURRENT SPOT */
  /* if should restore, restore, otherwise do not assert latentDB */
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(spaux);
  HMM_HSR * request = dynamic_cast<HMM_HSR *>(hsr);
  assert(aux);
  assert(request);

  /* No matter what the request is, we must sample the first latent if
     we have not already done so. */
  if (aux->xs.empty()) 
  { 
    aux->xs.push_back(sampleVectorXd(p0,rng));
  }

  if (aux->xs.size() <= request->index)
  {
    for (size_t i = aux->xs.size(); i <= request->index; ++i)
    {
      VectorXd sample;
      sample = sampleVectorXd(T * aux->xs.back(),rng);
      aux->xs.push_back(sample);
    }
  }
  assert(aux->xs.size() > request->index);
  return 0;
}

double LazyHMMSP::detachLatents(SPAux * spaux,
				HSR * hsr) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(spaux);
  HMM_HSR * request = dynamic_cast<HMM_HSR *>(hsr);

  assert(aux);
  assert(request);

  if (aux->xs.size() == request->index + 1 && 
      !aux->os.count(request->index))
  {
    if (aux->os.empty()) 
    { 
      aux->xs.clear();
    }
    else
    {
      uint32_t maxObservation = (*(max_element(aux->os.begin(),aux->os.end()))).first;
      for (size_t i = aux->xs.size()-1; i > maxObservation; --i)
      {
	aux->xs.pop_back();
      }
      assert(aux->xs.size() == maxObservation + 1);
    }
  }
  return 0;
}


VentureValue * LazyHMMSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(node->spaux());
  VentureNumber * vint = dynamic_cast<VentureNumber*>(args.operands[0]);
  assert(aux);
  assert(vint);

  assert(aux->xs.size() > vint->getInt());
  return new VentureAtom(sampleVector(O * aux->xs[vint->getInt()],rng));
}

double LazyHMMSP::logDensityOutput(VentureValue * value, const Args & args) const
{
  VentureAtom * vout = dynamic_cast<VentureAtom*>(value);
  VentureNumber * vin = dynamic_cast<VentureNumber*>(args.operands[0]);
  assert(vout);
  assert(vin);

  LazyHMMSPAux * aux = dynamic_cast<LazyHMMSPAux *>(node->spaux());

  assert(aux->xs.size() > vin->getInt());
  VectorXd dist = O * aux->xs[vin->getInt()];
  return log(dist[vout->n]);
}

VentureValue * LazyHMMSP::simulateRequest(const Args & args, gsl_rng * rng) const
{
  VentureNumber * vin = dynamic_cast<VentureNumber*>(args.operands[0]);
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
    if (u <= sum) 
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
    if (u <= sum) { return i; }
  }
  cout << "sum should be 1: " << sum << endl;
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
