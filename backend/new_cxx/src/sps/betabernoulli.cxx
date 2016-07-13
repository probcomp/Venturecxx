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

#include "sps/betabernoulli.h"

#include "utils.h"
#include "sprecord.h"
#include "stop-and-copy.h"

#include "gsl/gsl_sf_gamma.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include "sps/numerical_helpers.h"

#include <boost/math/special_functions/binomial.hpp>

VentureValuePtr MakeBetaBernoulliOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("make_beta_bernoulli", args, 2);

  double alpha = args->operandValues[0]->getDouble();
  double beta = args->operandValues[1]->getDouble();

  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new BetaBernoulliOutputPSP(alpha, beta);
  return VentureValuePtr(new VentureSPRecord(new SP(requestPSP, outputPSP), new SuffBernoulliSPAux()));
}

// BetaBernoulliOutputPSP

VentureValuePtr BetaBernoulliOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  shared_ptr<SuffBernoulliSPAux> aux = dynamic_pointer_cast<SuffBernoulliSPAux>(args->spAux);
  double a = alpha + aux->heads;
  double b = beta + aux->tails;
  double w = a / (a + b);
  return VentureValuePtr(new VentureBool(gsl_ran_flat(rng, 0.0, 1.0) < w));
}

double BetaBernoulliOutputPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  shared_ptr<SuffBernoulliSPAux> aux = dynamic_pointer_cast<SuffBernoulliSPAux>(args->spAux);
  double a = alpha + aux->heads;
  double b = beta + aux->tails;
  double w = a / (a + b);
  if (value->getBool()) { return log(w); }
  else { return log1p(-w); }
}

void BetaBernoulliOutputPSP::incorporate(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  shared_ptr<SuffBernoulliSPAux> aux = dynamic_pointer_cast<SuffBernoulliSPAux>(args->spAux);
  if (value->getBool()) { aux->heads++; }
  else { aux->tails++; }
}
void BetaBernoulliOutputPSP::unincorporate(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  shared_ptr<SuffBernoulliSPAux> aux = dynamic_pointer_cast<SuffBernoulliSPAux>(args->spAux);
  if (value->getBool()) { aux->heads--; }
  else { aux->tails--; }
}

double BetaBernoulliOutputPSP::logDensityOfData(shared_ptr<SPAux> aux) const
{
  shared_ptr<SuffBernoulliSPAux> spAux = dynamic_pointer_cast<SuffBernoulliSPAux>(aux);


  int heads = spAux->heads;
  int tails = spAux->tails;

  int N = heads + tails;
  double A = alpha + beta;

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  x += gsl_sf_lngamma(alpha + heads) - gsl_sf_lngamma(alpha);
  x += gsl_sf_lngamma(beta + tails) - gsl_sf_lngamma(beta);
  return x;
}

// MakeUncollapsed

VentureValuePtr MakeUBetaBernoulliOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 2);

  double alpha = args->operandValues[0]->getDouble();
  double beta = args->operandValues[1]->getDouble();

  double p = gsl_ran_beta(rng, alpha, beta);

  USuffBernoulliSPAux * aux = new USuffBernoulliSPAux(p);
  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new SuffBernoulliOutputPSP();
  return VentureValuePtr(new VentureSPRecord(new UBetaBernoulliSP(requestPSP, outputPSP), aux));
}

double MakeUBetaBernoulliOutputPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  assert(args->operandValues.size() == 2);

  double alpha = args->operandValues[0]->getDouble();
  double beta = args->operandValues[1]->getDouble();

  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(value);
  assert(spRecord);
  shared_ptr<USuffBernoulliSPAux> spAux = dynamic_pointer_cast<USuffBernoulliSPAux>(spRecord->spAux);
  assert(spAux);

  return BetaDistributionLogLikelihood(spAux->p, alpha, beta);
}

// Uncollapsed SP

void UBetaBernoulliSP::AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 2);
  shared_ptr<USuffBernoulliSPAux> aux = dynamic_pointer_cast<USuffBernoulliSPAux>(spAux);

  double alpha = args->operandValues[0]->getDouble();
  double beta = args->operandValues[1]->getDouble();

  int heads = aux->heads;
  int tails = aux->tails;

  aux->p = gsl_ran_beta(rng, alpha + heads, beta + tails);
}

UBetaBernoulliSP* UBetaBernoulliSP::copy_help(ForwardingMap* forward) const
{
  UBetaBernoulliSP* answer = new UBetaBernoulliSP(*this);
  (*forward)[this] = answer;
  answer->requestPSP = copy_shared(this->requestPSP, forward);
  answer->outputPSP = copy_shared(this->outputPSP, forward);
  return answer;
}

// Uncollapsed PSP

VentureValuePtr SuffBernoulliOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  shared_ptr<USuffBernoulliSPAux> aux = dynamic_pointer_cast<USuffBernoulliSPAux>(args->spAux);
  int n = gsl_ran_bernoulli(rng, aux->p);
  if (n == 0) { return VentureValuePtr(new VentureBool(false)); }
  else if (n == 1) { return VentureValuePtr(new VentureBool(true)); }
  else { assert(false); }
}

double SuffBernoulliOutputPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  shared_ptr<USuffBernoulliSPAux> aux = dynamic_pointer_cast<USuffBernoulliSPAux>(args->spAux);
  double p = aux->p;
  if (value->getBool()) { return log(p); }
  else { return log1p(-p); }
}

void SuffBernoulliOutputPSP::incorporate(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  shared_ptr<USuffBernoulliSPAux> aux = dynamic_pointer_cast<USuffBernoulliSPAux>(args->spAux);
  if (value->getBool()) { aux->heads++; }
  else { aux->tails++; }
}

void SuffBernoulliOutputPSP::unincorporate(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  shared_ptr<USuffBernoulliSPAux> aux = dynamic_pointer_cast<USuffBernoulliSPAux>(args->spAux);
  if (value->getBool()) { aux->heads--; }
  else { aux->tails--; }
}

// Auxs
VentureValuePtr SuffBernoulliSPAux::asVentureValue() const
{
  VentureValuePtr hd(new VentureNumber(heads));
  VentureValuePtr tl(new VentureNumber(tails));
  VentureValuePtr end(new VentureNil());

  return VentureValuePtr(new VenturePair(hd, VentureValuePtr(new VenturePair(tl, end))));
}

SuffBernoulliSPAux* SuffBernoulliSPAux::copy_help(ForwardingMap* m) const
{
  SuffBernoulliSPAux* answer = new SuffBernoulliSPAux(*this);
  (*m)[this] = answer;
  return answer;
}

USuffBernoulliSPAux* USuffBernoulliSPAux::copy_help(ForwardingMap* m) const
{
  USuffBernoulliSPAux* answer = new USuffBernoulliSPAux(*this);
  (*m)[this] = answer;
  return answer;
}
