#ifndef SPS_BETA_BERNOULLI_H
#define SPS_BETA_BERNOULLI_H

#include "types.h"
#include "psp.h"
#include "args.h"
#include "sp.h"

// Collapsed SPAux
struct BetaBernoulliSPAux : SPAux
{
 BetaBernoulliSPAux(): heads(0), tails(0) {}
  shared_ptr<SPAux> clone();

  int heads;
  int tails;
};

struct MakeBetaBernoulliOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};


struct BetaBernoulliOutputPSP : RandomPSP
{
 BetaBernoulliOutputPSP(double alpha, double beta) : alpha(alpha), beta(beta) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  double logDensityOfCounts(shared_ptr<SPAux> spAux) const;

private:
  double alpha;
  double beta;
};

// Uncollapsed SPAux
struct UBetaBernoulliSPAux : BetaBernoulliSPAux
{
 UBetaBernoulliSPAux(double p): BetaBernoulliSPAux(), p(p) {}
  shared_ptr<SPAux> clone();

  double p;
};

// Uncollapsed
struct MakeUBetaBernoulliOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct UBetaBernoulliSP : SP
{
  UBetaBernoulliSP(PSP * requestPSP, PSP * outputPSP): SP(requestPSP,outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<Args> args,gsl_rng * rng) const;
};

struct UBetaBernoulliOutputPSP : RandomPSP
{
  UBetaBernoulliOutputPSP() {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

};




#endif
