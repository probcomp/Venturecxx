#ifndef MAKE_BETA_BERNOULLI_H
#define MAKE_BETA_BERNOULLI_H

#include "sp.h"
#include "spaux.h"
#include <vector>
#include <string>

struct BetaBernoulliSPAux : SPAux
{
  BetaBernoulliSPAux(uint32_t n): counts(n,0) {}
  vector<uint32_t> counts;
};

struct MakeBetaBernoulliSP : SP
{
  MakeBetaBernoulliSP()
    {
      childrenCanAAA = true;
      name = "make_beta_bernoulli";
    }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;

};

struct BetaBernoulliSP : SP
{
  BetaBernoulliSP(vector<double> alphaVector): alphaVector(alphaVector)
    {
      isRandomOutput = true;
      canAbsorbOutput = true;
      tracksSamples = true;
      name = "beta_bernoulli";
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, Node * node) const override;
  void incorporateOutput(VentureValue * value, Node * node) const override;
  void removeOutput(VentureValue * value, Node * node) const override;

  double logDensityOfCounts(SPAux * spaux) const;

  SPAux * constructSPAux() const override;
  void destroySPAux(SPAux * spaux) const override;

  vector<double> alphaVector;

};



#endif
