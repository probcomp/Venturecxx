#include "sps/dir_mult.h"
#include "sprecord.h"
#include "utils.h"
#include "gsl/gsl_sf_gamma.h"

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

