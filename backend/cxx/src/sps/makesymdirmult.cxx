#include "value.h"
#include "utils.h"
#include "node.h"
#include "sp.h"
#include "sps/makesymdirmult.h"
#include "gsl/gsl_sf_gamma.h"

#include<boost/range/numeric.hpp>

SymDirMultSPAux * SymDirMultSPAux::clone()
{
  SymDirMultSPAux * aux = new SymDirMultSPAux(counts.size());
  aux->families = families;
  aux->ownedValues = ownedValues;
  aux->counts = counts;
  return aux
}


VentureValue * MakeSymDirMultSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * n = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(alpha);
  assert(n);
  return new VentureSP(new SymDirMultSP(alpha->x,static_cast<uint32_t>(n->x)));
}



double SymDirMultSP::logDensityOfCounts(SPAux * generic_spaux) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(generic_spaux);
  assert(spaux);

  auto N = boost::accumulate(spaux->counts, 0);
  double A = alpha * spaux->counts.size();

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  for (auto count : spaux->counts)
  {
    x += gsl_sf_lngamma(alpha + count) - gsl_sf_lngamma(alpha);
  }
  return x;
}

VentureValue * SymDirMultSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  vector<double> xs;
  for (auto x : spaux->counts)
  {
    xs.push_back(x + alpha);
  }
  normalizeVector(xs);
  return new VentureAtom(sampleCategorical(xs,rng));
}

double SymDirMultSP::logDensityOutput(VentureValue * value, const Args & args) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;

  vector<double> xs;
  for (auto x : spaux->counts)
  {
    xs.push_back(x + alpha);
  }
  normalizeVector(xs);
  return log(xs[observedIndex]);
}

void SymDirMultSP::incorporateOutput(VentureValue * value, const Args & args) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]++;
}

void SymDirMultSP::removeOutput(VentureValue * value, const Args & args) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]--;
}

SPAux * SymDirMultSP::constructSPAux() const
{
  return new SymDirMultSPAux(n);
}

void SymDirMultSP::destroySPAux(SPAux *spaux) const
{
  delete spaux;
}
