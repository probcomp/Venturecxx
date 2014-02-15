#include "sps/dir_mult.h"
#include "sprecord.h"
#include "utils.h"
#include "gsl/gsl_sf_gamma.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include<boost/range/numeric.hpp>

/* DirMultSPAux */
DirMultSPAux::DirMultSPAux(int n) : counts(n, 0) {}

/* DirMultOutputPSP */
VentureValuePtr DirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const { assert(false); }
double DirMultOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const { assert(false); }

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

  int N = boost::accumulate(aux->counts, 0);
  double A = alpha * n;

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A) - n * gsl_sf_lngamma(alpha);
  for (size_t i = 0; i < n; ++i)
  {
    x += gsl_sf_lngamma(alpha + aux->counts[i]);
  }
  return x;
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

////////////////// Uncollapsed

void UCSymDirMultSP::AEInfer(shared_ptr<SPAux> madeSPAux) const { assert(false); }

VentureValuePtr MakeUCSymDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 2); // TODO optional 3rd argument
  
  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();
  
  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new SymDirMultOutputPSP(alpha, n);
  SP * sp = new UCSymDirMultSP(requestPSP,outputPSP);

  uint32_t d = static_cast<uint32_t>(n);

  double *alphaVector = new double[d];
  for (size_t i = 0; i < d; ++i) { alphaVector[i] = alpha; }

  /* TODO GC watch the NEW */
  double *theta = new double[d];

  gsl_ran_dirichlet(rng,d,alphaVector,theta);

  delete[] alphaVector;

  SPAux * spAux = new UCDirMultSPAux(n,theta);
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

  uint32_t d = static_cast<uint32_t>(n);

  double *alphaVector = new double[d];
  for (size_t i = 0; i < d; ++i) { alphaVector[i] = alpha; }

  double ld = gsl_ran_dirichlet_lnpdf(d,alphaVector,spAux->theta);
  delete[] alphaVector;
  return ld;
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
