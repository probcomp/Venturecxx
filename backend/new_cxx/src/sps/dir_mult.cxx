#include "sps/dir_mult.h"
#include "sprecord.h"
#include "utils.h"
#include "gsl/gsl_sf_gamma.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include<boost/range/numeric.hpp>

// Collapsed Symmetric

/* MakeSymDirMultOutputPSP */
VentureValuePtr MakeSymDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 2); // TODO throw an error once exceptions work
  
  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();
  
  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new SymDirMultOutputPSP(alpha, n);
  return VentureValuePtr(new VentureSPRecord(new SP(requestPSP,outputPSP),new DirMultSPAux(n)));
}

/* SymDirMultOutputPSP */
VentureValuePtr SymDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);
  
  vector<double> weights(n, alpha);
  for (size_t i = 0; i < n; ++i) {
    weights[i] += aux->counts[i];
  }
  
  return simulateCategorical(weights, rng);
}

double SymDirMultOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  vector<double> xs;
  for (size_t i = 0; i < n ; ++i)
  {
    xs.push_back(aux->counts[i] + alpha);
  }
  xs = normalizeVector(xs);
  return log(xs[value->getInt()]);
}

void SymDirMultOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);
  
  int index = value->getInt();
  aux->counts[index]++;
}

void SymDirMultOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);
  
  int index = value->getInt();
  aux->counts[index]--;
  
  assert(aux->counts[index] >= 0);
}

double SymDirMultOutputPSP::logDensityOfCounts(shared_ptr<SPAux> spAux) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(spAux);
  assert(aux);

  int N = boost::accumulate(aux->counts, 0);
  double A = alpha * n;

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  for (size_t i = 0; i < n; ++i)
  {
    x += gsl_sf_lngamma(alpha + aux->counts[i]);
  }
  x -= n * gsl_sf_lngamma(alpha);
  return x;
}

// Collapsed Asymmetric

/* MakeDirMultOutputPSP */
VentureValuePtr MakeDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 1); // TODO throw an error once exceptions work
  
  shared_ptr<VentureArray> alphaArray = dynamic_pointer_cast<VentureArray>(args->operandValues[0]);
  assert(alphaArray);
  
  size_t n = alphaArray->xs.size();
  vector<double> alpha;
  alpha.reserve(n);
  
  for (size_t i = 0; i < n; ++i)
  {
    alpha.push_back(alphaArray->xs[i]->getDouble());
  }
  
  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new DirMultOutputPSP(alpha);
  
  return VentureValuePtr(new VentureSPRecord(new SP(requestPSP,outputPSP),new DirMultSPAux(n)));
}

/* DirMultOutputPSP */
VentureValuePtr DirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == alpha.size());
  
  vector<double> weights(alpha);
  for (size_t i = 0; i < alpha.size(); ++i)
  {
    weights[i] += aux->counts[i];
  }
  
  return simulateCategorical(weights, rng);
}

double DirMultOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == alpha.size());

  vector<double> weights(alpha);
  for (size_t i = 0; i < alpha.size(); ++i)
  {
    weights[i] += aux->counts[i];
  }
  weights = normalizeVector(weights);
  return log(weights[value->getInt()]);
}

void DirMultOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == alpha.size());
  
  int index = value->getInt();
  aux->counts[index]++;
}

void DirMultOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == alpha.size());
  
  int index = value->getInt();
  aux->counts[index]--;
  
  assert(aux->counts[index] >= 0);
}

double DirMultOutputPSP::logDensityOfCounts(shared_ptr<SPAux> spAux) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(spAux);
  assert(aux);

  int N = boost::accumulate(aux->counts, 0);
  double A = boost::accumulate(alpha, 0);

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  for (size_t i = 0; i < alpha.size(); ++i)
  {
    x += gsl_sf_lngamma(alpha[i] + aux->counts[i]);
    x -= gsl_sf_lngamma(alpha[i]);
  }
  return x;
}

////////////////// Uncollapsed

VentureValuePtr MakeUCSymDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 2); // TODO optional 3rd argument
  
  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();
  
  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new UCSymDirMultOutputPSP(n);
  SP * sp = new UCSymDirMultSP(requestPSP,outputPSP);

  vector<double> alphaVector(n, alpha);

  UCDirMultSPAux * spAux = new UCDirMultSPAux(n);

  gsl_ran_dirichlet(rng,n,&alphaVector[0],&spAux->theta[0]);

  return VentureValuePtr(new VentureSPRecord(sp,spAux));
}

double MakeUCSymDirMultOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  assert(args->operandValues.size() == 2); // TODO optional 3rd argument
  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();

  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(value);
  assert(spRecord);
  shared_ptr<UCDirMultSPAux> spAux = dynamic_pointer_cast<UCDirMultSPAux>(spRecord->spAux);
  assert(spAux);

  vector<double> alphaVector(n, alpha);
  assert(alphaVector.size() == spAux->counts.size());

  return gsl_ran_dirichlet_lnpdf(n,&alphaVector[0],&spAux->theta[0]);
}

// Note: odd design
// It gets the args 
void UCSymDirMultSP::AEInfer(shared_ptr<Args> args,gsl_rng * rng) const 
{ 
  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();

  shared_ptr<UCDirMultSPAux> spAux = dynamic_pointer_cast<UCDirMultSPAux>(args->madeSPAux);
  assert(spAux);

  uint32_t d = static_cast<uint32_t>(n);
  assert(spAux->counts.size() == d);

  double *conjAlphaVector = new double[d];

  for (size_t i = 0; i < d; ++i) 
  { 
    conjAlphaVector[i] = alpha + spAux->counts[i];
  }

  gsl_ran_dirichlet(rng,d,conjAlphaVector,&spAux->theta[0]);

  delete[] conjAlphaVector;
}

VentureValuePtr UCSymDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  shared_ptr<UCDirMultSPAux> aux = dynamic_pointer_cast<UCDirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < n; ++i)
  {
    sum += aux->theta[i];
    if (u < sum) { return VentureValuePtr(new VentureAtom(i)); }
  }
  assert(false);
  return VentureValuePtr();
}

double UCSymDirMultOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<UCDirMultSPAux> aux = dynamic_pointer_cast<UCDirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  return log(aux->theta[value->getInt()]);
}

void UCSymDirMultOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);
  
  int index = value->getInt();
  aux->counts[index]++;
}

void UCSymDirMultOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);
  
  int index = value->getInt();
  aux->counts[index]--;
  
  assert(aux->counts[index] >= 0);
}

// Uncollapsed Asymmetric

VentureValuePtr MakeUCDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 1); // TODO optional 2nd argument
  
  shared_ptr<VentureArray> alphaArray = dynamic_pointer_cast<VentureArray>(args->operandValues[0]);
  assert(alphaArray);
  size_t n = alphaArray->xs.size();
  
  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new UCDirMultOutputPSP(n);
  SP * sp = new UCDirMultSP(requestPSP,outputPSP);

  double *alphaVector = new double[n];
  for (size_t i = 0; i < n; ++i)
  {
    alphaVector[i] = alphaArray->xs[i]->getDouble();
  }
  
  UCDirMultSPAux * spAux = new UCDirMultSPAux(n);

  gsl_ran_dirichlet(rng,n,alphaVector,&spAux->theta[0]);

  delete[] alphaVector;
  
  return VentureValuePtr(new VentureSPRecord(sp,spAux));
}

double MakeUCDirMultOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  assert(args->operandValues.size() == 1); // TODO optional 2nd argument
  
  shared_ptr<VentureArray> alphaArray = dynamic_pointer_cast<VentureArray>(args->operandValues[0]);
  assert(alphaArray);
  size_t n = alphaArray->xs.size();

  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(value);
  assert(spRecord);
  shared_ptr<UCDirMultSPAux> spAux = dynamic_pointer_cast<UCDirMultSPAux>(spRecord->spAux);
  assert(spAux);

  double *alphaVector = new double[n];
  for (size_t i = 0; i < n; ++i)
  {
    alphaVector[i] = alphaArray->xs[i]->getDouble();
  }

  double ld = gsl_ran_dirichlet_lnpdf(n,alphaVector,&spAux->theta[0]);
  delete[] alphaVector;
  return ld;
}

void UCDirMultSP::AEInfer(shared_ptr<Args> args,gsl_rng * rng) const 
{
  shared_ptr<VentureArray> alphaArray = dynamic_pointer_cast<VentureArray>(args->operandValues[0]);
  assert(alphaArray);
  size_t n = alphaArray->xs.size();
  
  shared_ptr<UCDirMultSPAux> spAux = dynamic_pointer_cast<UCDirMultSPAux>(args->madeSPAux);
  assert(spAux);
  assert(spAux->counts.size() == n);

  double * conjAlphaVector = new double[n];
  for (size_t i = 0; i < n; ++i)
  { 
    conjAlphaVector[i] = spAux->counts[i] + alphaArray->xs[i]->getDouble();
  }

  gsl_ran_dirichlet(rng,n,conjAlphaVector,&spAux->theta[0]);
}

VentureValuePtr UCDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  shared_ptr<UCDirMultSPAux> aux = dynamic_pointer_cast<UCDirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < n; ++i)
  {
    sum += aux->theta[i];
    if (u < sum) { return VentureValuePtr(new VentureAtom(i)); }
  }
  assert(false);
  return VentureValuePtr();
}

double UCDirMultOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<UCDirMultSPAux> aux = dynamic_pointer_cast<UCDirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  return log(aux->theta[value->getInt()]);
}

void UCDirMultOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);
  
  int index = value->getInt();
  aux->counts[index]++;
}

void UCDirMultOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);
  
  int index = value->getInt();
  aux->counts[index]--;
  
  assert(aux->counts[index] >= 0);
}

// Aux clones
shared_ptr<SPAux> DirMultSPAux::clone() { return shared_ptr<SPAux>(new DirMultSPAux(*this)); }
shared_ptr<SPAux> UCDirMultSPAux::clone() { return shared_ptr<SPAux>(new UCDirMultSPAux(*this)); }
