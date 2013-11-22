#include "value.h"
#include "utils.h"

#include "sp.h"
#include "sps/makedirmult.h"
#include "sps/makesymdirmult.h"
#include "gsl/gsl_sf_gamma.h"

#include<boost/range/numeric.hpp>

VentureValue * MakeDirMultSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  vector<double> alphaVector;
  for (VentureValue * operand : args.operands)
  {
    VentureNumber * alpha_i = dynamic_cast<VentureNumber *>(operand);
    assert(alpha_i);
    alphaVector.push_back(alpha_i->x);
  }

  return new VentureSP(new DirMultSP(alphaVector));
}

double DirMultSP::logDensityOfCounts(SPAux * generic_spaux) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(generic_spaux);
  assert(spaux);

  auto N = boost::accumulate(spaux->counts, 0);
  double A = boost::accumulate(alphaVector, 0);

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    x += gsl_sf_lngamma(alphaVector[i] + spaux->counts[i]) - gsl_sf_lngamma(alphaVector[i]);
  }
  return x;
}

VentureValue * DirMultSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(args.spaux);
  assert(spaux);

  vector<double> xs;
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    xs.push_back(alphaVector[i] + spaux->counts[i]);
  }
  normalizeVector(xs);
  return new VentureAtom(sampleCategorical(xs,rng));
}

double DirMultSP::logDensityOutput(VentureValue * value, const Args & args) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(args.spaux);
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;

  vector<double> xs;
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    xs.push_back(alphaVector[i] + spaux->counts[i]);
  }
  normalizeVector(xs);
  return log(xs[observedIndex]);
}

void DirMultSP::incorporateOutput(VentureValue * value, const Args & args) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(args.spaux);
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]++;
}

void DirMultSP::removeOutput(VentureValue * value, const Args & args) const
{
  assert(args.spaux);
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(args.spaux);
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]--;
}

SPAux * DirMultSP::constructSPAux() const
{
  return new SymDirMultSPAux(alphaVector.size());
}

void DirMultSP::destroySPAux(SPAux *spaux) const
{
  delete spaux;
}
