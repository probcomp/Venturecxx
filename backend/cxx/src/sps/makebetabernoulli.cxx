#include "value.h"
#include "utils.h"
#include "node.h"
#include "sp.h"
#include "sps/makebetabernoulli.h"
#include "gsl/gsl_sf_gamma.h"

#include<boost/range/numeric.hpp>

VentureValue * MakeBetaBernoulliSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  vector<double> alphaVector;
  for (Node * operandNode : args.operands)
  {
    VentureNumber * alpha_i = dynamic_cast<VentureNumber *>(operandNode);
    assert(alpha_i);
    alphaVector.push_back(alpha_i->x);
  }
  assert(alphaVector.size() == 2);

  return new VentureSP(new BetaBernoulliSP(alphaVector));
}

double BetaBernoulliSP::logDensityOfCounts(SPAux * generic_spaux) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(generic_spaux);
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

VentureValue * BetaBernoulliSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(node->spaux());
  assert(spaux);

  vector<double> xs;
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    xs.push_back(alphaVector[i] + spaux->counts[i]);
  }
  normalizeVector(xs);

  uint32_t n = sampleCategorical(xs,rng);
  return new VentureBool(n == 1);
}

double BetaBernoulliSP::logDensityOutput(VentureValue * value, const Args & args) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(node->spaux());
  assert(spaux);

  VentureBool * vb = dynamic_cast<VentureBool*>(value);
  assert(vb);
  uint32_t observedIndex = vb->pred ? 1 : 0;

  vector<double> xs;
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    xs.push_back(alphaVector[i] + spaux->counts[i]);
  }
  normalizeVector(xs);
  return log(xs[observedIndex]);
}

void BetaBernoulliSP::incorporateOutput(VentureValue * value, const Args & args) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(node->spaux());
  assert(spaux);

  VentureBool * vb = dynamic_cast<VentureBool*>(value);
  assert(vb);
  uint32_t observedIndex = vb->pred ? 1 : 0;

  spaux->counts[observedIndex]++;
}

void BetaBernoulliSP::removeOutput(VentureValue * value, const Args & args) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(node->spaux());
  assert(spaux);

  VentureBool * vb = dynamic_cast<VentureBool*>(value);
  assert(vb);
  uint32_t observedIndex = vb->pred ? 1 : 0;

  spaux->counts[observedIndex]--;
}

SPAux * BetaBernoulliSP::constructSPAux() const
{
  return new BetaBernoulliSPAux(alphaVector.size());
}

void BetaBernoulliSP::destroySPAux(SPAux *spaux) const
{
  delete spaux;
}
