#ifndef MAKE_BETA_BERNOULLI_H
#define MAKE_BETA_BERNOULLI_H

#include "sp.h"
#include "spaux.h"
#include <vector>
#include <string>

struct MakeBetaBernoulliSP : SP
{
  MakeBetaBernoulliSP()
    {
      childrenCanAAA = true;
      name = "make_beta_bernoulli";
    }
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;

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

  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;
  void incorporateOutput(VentureValue * value, const Args & args) const override;
  void removeOutput(VentureValue * value, const Args & args) const override;

  double logDensityOfCounts(SPAux * spaux) const;

  SPAux * constructSPAux() const override;
  void destroySPAux(SPAux * spaux) const override;

  vector<double> alphaVector;

};



#endif
