// Copyright (c) 2014, 2015, 2016 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#ifndef SPS_BETA_BERNOULLI_H
#define SPS_BETA_BERNOULLI_H

#include "types.h"
#include "psp.h"
#include "args.h"
#include "sp.h"

// Collapsed SPAux
struct SuffBernoulliSPAux : SPAux
{
  SuffBernoulliSPAux(): heads(0), tails(0) {}
  VentureValuePtr asVentureValue() const;
  SuffBernoulliSPAux* copy_help(ForwardingMap* m) const;

  int heads;
  int tails;
};

struct MakeBetaBernoulliOutputPSP : virtual PSP
  , DeterministicMakerAAAPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};


struct BetaBernoulliOutputPSP : virtual RandomPSP
{
  BetaBernoulliOutputPSP(double alpha, double beta) : alpha(alpha), beta(beta) {}

  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  double logDensity(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
  void incorporate(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
  void unincorporate(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;

  double logDensityOfData(shared_ptr<SPAux> spAux) const;

private:
  const double alpha;
  const double beta;
};

// Uncollapsed SPAux
struct USuffBernoulliSPAux : SuffBernoulliSPAux
{
  USuffBernoulliSPAux(double p): SuffBernoulliSPAux(), p(p) {}
  USuffBernoulliSPAux* copy_help(ForwardingMap* m) const;

  double p;
};

// Uncollapsed
struct MakeUBetaBernoulliOutputPSP : virtual RandomPSP
  , DefaultIncorporatePSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  double logDensity(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
};

struct UBetaBernoulliSP : SP
{
  UBetaBernoulliSP(PSP * requestPSP, PSP * outputPSP): SP(requestPSP, outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args, gsl_rng * rng) const;
  UBetaBernoulliSP* copy_help(ForwardingMap* m) const;
};

struct SuffBernoulliOutputPSP : virtual RandomPSP
{
  SuffBernoulliOutputPSP() {}

  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  double logDensity(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
  void incorporate(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
  void unincorporate(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;

};




#endif
