// Copyright (c) 2014 MIT Probabilistic Computing Project.
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

#include "sps/dir_mult.h"
#include "sprecord.h"
#include "utils.h"
#include "gsl/gsl_sf_gamma.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include<boost/range/numeric.hpp>

boost::python::object DirMultSPAux::toPython(Trace * trace) const
{
  return toPythonList(trace, counts);
}

// Collapsed Symmetric

/* MakeSymDirMultOutputPSP */
VentureValuePtr MakeSymDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("make_sym_dir_mult", args, 2);

  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();
  return VentureValuePtr(new VentureSPRecord(new SymDirMultSP(alpha, n),new DirMultSPAux(n)));
}

SymDirMultSP::SymDirMultSP(double alpha, size_t n) : SP(new NullRequestPSP(), new SymDirMultOutputPSP(alpha, n)), alpha(alpha), n(n) {}

boost::python::dict SymDirMultSP::toPython(Trace * trace, shared_ptr<SPAux> spAux) const
{
  boost::python::dict symDirMult;
  symDirMult["type"] = "sym_dir_mult";
  symDirMult["alpha"] = alpha;
  symDirMult["n"] = n;
  symDirMult["counts"] = spAux->toPython(trace);

  boost::python::dict value;
  value["type"] = "sp";
  value["value"] = symDirMult;

  return value;
}

/* SymDirMultOutputPSP */
VentureValuePtr SymDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("sym_dir_mult", args, 0);

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

  int index = value->getInt();
  double num = aux->counts[index] + alpha;
  double denom = aux->total + alpha * n;
  return log(num/denom);
}

void SymDirMultOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  int index = value->getInt();
  aux->counts[index]++;
  aux->total++;
}

void SymDirMultOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  int index = value->getInt();
  aux->counts[index]--;
  aux->total--;

  assert(aux->counts[index] >= 0);
}

vector<VentureValuePtr> SymDirMultOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  vector<VentureValuePtr> vs;
  for (size_t i = 0; i < n; ++i) {
    vs.push_back(VentureValuePtr(new VentureAtom(i)));
  }
  return vs;
}

double SymDirMultOutputPSP::logDensityOfCounts(shared_ptr<SPAux> spAux) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(spAux);
  assert(aux);

  int N = aux->total;
  double A = alpha * n;

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  for (size_t i = 0; i < n; ++i)
  {
    x += gsl_sf_lngamma(alpha + aux->counts[i]);
  }
  x -= n * gsl_sf_lngamma(alpha);
  return x;
}

// Collapsed Asymmetric

/* MakeDirMultOutputPSP */
VentureValuePtr MakeDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("make_dir_mult", args, 1);

  vector<double> alpha;
  BOOST_FOREACH(VentureValuePtr v, args->operandValues[0]->getArray())
  {
    alpha.push_back(v->getDouble());
  }

  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new DirMultOutputPSP(alpha, boost::accumulate(alpha, 0));

  return VentureValuePtr(new VentureSPRecord(new SP(requestPSP,outputPSP),new DirMultSPAux(alpha.size())));
}

/* DirMultOutputPSP */
VentureValuePtr DirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("dir_mult", args, 0);

  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == alpha.size());

  vector<double> weights(alpha);
  for (size_t i = 0; i < alpha.size(); ++i)
  {
    weights[i] += aux->counts[i];
  }

  return simulateCategorical(weights, rng);
}

double DirMultOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == alpha.size());

  int index = value->getInt();
  double num = aux->counts[index] + alpha[index];
  double denom = aux->total + total;
  return log(num/denom);
}

void DirMultOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == alpha.size());

  int index = value->getInt();
  aux->counts[index]++;
  aux->total++;
}

void DirMultOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == alpha.size());

  int index = value->getInt();
  aux->counts[index]--;
  aux->total--;

  assert(aux->counts[index] >= 0);
}

vector<VentureValuePtr> DirMultOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  vector<VentureValuePtr> vs;
  for (size_t i = 0; i < alpha.size(); ++i) {
    vs.push_back(VentureValuePtr(new VentureAtom(i)));
  }
  return vs;
}

double DirMultOutputPSP::logDensityOfCounts(shared_ptr<SPAux> spAux) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(spAux);
  assert(aux);

  int N = aux->total;
  double A = total;

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  for (size_t i = 0; i < alpha.size(); ++i)
  {
    x += gsl_sf_lngamma(alpha[i] + aux->counts[i]);
    x -= gsl_sf_lngamma(alpha[i]);
  }
  return x;
}

// Uncollapsed

VentureValuePtr MakeUCSymDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  // TODO optional 3rd argument
  checkArgsLength("make_uc_sym_dir_mult", args, 2);

  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();

  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new UCSymDirMultOutputPSP(n);
  SP * sp = new UCSymDirMultSP(requestPSP,outputPSP);

  vector<double> alphaVector(n, alpha);

  UCDirMultSPAux * spAux = new UCDirMultSPAux(n);

  gsl_ran_dirichlet(rng,n,&alphaVector[0],&spAux->theta[0]);

  return VentureValuePtr(new VentureSPRecord(sp,spAux));
}

double MakeUCSymDirMultOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  checkArgsLength("make_uc_sym_dir_mult", args, 2);

  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();

  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(value);
  assert(spRecord);
  shared_ptr<UCDirMultSPAux> spAux = dynamic_pointer_cast<UCDirMultSPAux>(spRecord->spAux);
  assert(spAux);

  vector<double> alphaVector(n, alpha);
  assert(alphaVector.size() == spAux->counts.size());

  return gsl_ran_dirichlet_lnpdf(n,&alphaVector[0],&spAux->theta[0]);
}

// Note: odd design
// It gets the args
void UCSymDirMultSP::AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,gsl_rng * rng) const
{
  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();

  shared_ptr<UCDirMultSPAux> aux = dynamic_pointer_cast<UCDirMultSPAux>(spAux);
  assert(aux);

  uint32_t d = static_cast<uint32_t>(n);
  assert(aux->counts.size() == d);

  double *conjAlphaVector = new double[d];

  for (size_t i = 0; i < d; ++i)
  {
    conjAlphaVector[i] = alpha + aux->counts[i];
  }

  gsl_ran_dirichlet(rng,d,conjAlphaVector,&aux->theta[0]);

  delete[] conjAlphaVector;
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

vector<VentureValuePtr> UCSymDirMultOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  vector<VentureValuePtr> vs;
  for (size_t i = 0; i < n; ++i) {
    vs.push_back(VentureValuePtr(new VentureAtom(i)));
  }
  return vs;
}

// Uncollapsed Asymmetric

VentureValuePtr MakeUCDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  // TODO optional 2nd argument
  checkArgsLength("make_uc_dir_mult", args, 1);

  const vector<VentureValuePtr>& alphaArray = args->operandValues[0]->getArray();
  size_t n = alphaArray.size();

  double* alphaVector = new double[n];
  for (size_t i = 0; i < n; ++i)
  {
    alphaVector[i] = alphaArray[i]->getDouble();
  }

  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new UCDirMultOutputPSP(n);
  SP * sp = new UCDirMultSP(requestPSP,outputPSP);

  UCDirMultSPAux * spAux = new UCDirMultSPAux(n);

  gsl_ran_dirichlet(rng,n,alphaVector,&spAux->theta[0]);

  delete[] alphaVector;

  return VentureValuePtr(new VentureSPRecord(sp,spAux));
}

double MakeUCDirMultOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  // TODO optional 2nd argument
  checkArgsLength("make_uc_dir_mult", args, 1);

  shared_ptr<VentureArray> alphaArray = dynamic_pointer_cast<VentureArray>(args->operandValues[0]);
  assert(alphaArray);
  size_t n = alphaArray->xs.size();

  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(value);
  assert(spRecord);
  shared_ptr<UCDirMultSPAux> spAux = dynamic_pointer_cast<UCDirMultSPAux>(spRecord->spAux);
  assert(spAux);

  double *alphaVector = new double[n];
  for (size_t i = 0; i < n; ++i)
  {
    alphaVector[i] = alphaArray->xs[i]->getDouble();
  }

  double ld = gsl_ran_dirichlet_lnpdf(n,alphaVector,&spAux->theta[0]);
  delete[] alphaVector;
  return ld;
}

void UCDirMultSP::AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,gsl_rng * rng) const
{
  shared_ptr<VentureArray> alphaArray = dynamic_pointer_cast<VentureArray>(args->operandValues[0]);
  assert(alphaArray);
  size_t n = alphaArray->xs.size();

  shared_ptr<UCDirMultSPAux> aux = dynamic_pointer_cast<UCDirMultSPAux>(spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  double * conjAlphaVector = new double[n];
  for (size_t i = 0; i < n; ++i)
  {
    conjAlphaVector[i] = aux->counts[i] + alphaArray->xs[i]->getDouble();
  }

  gsl_ran_dirichlet(rng,n,conjAlphaVector,&aux->theta[0]);
}

VentureValuePtr UCDirMultOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("uc_dir_mult", args, 0);

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

double UCDirMultOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<UCDirMultSPAux> aux = dynamic_pointer_cast<UCDirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  return log(aux->theta[value->getInt()]);
}

void UCDirMultOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  int index = value->getInt();
  aux->counts[index]++;
}

void UCDirMultOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<DirMultSPAux> aux = dynamic_pointer_cast<DirMultSPAux>(args->spAux);
  assert(aux);
  assert(aux->counts.size() == n);

  int index = value->getInt();
  aux->counts[index]--;

  assert(aux->counts[index] >= 0);
}

vector<VentureValuePtr> UCDirMultOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  vector<VentureValuePtr> vs;
  for (size_t i = 0; i < n; ++i) {
    vs.push_back(VentureValuePtr(new VentureAtom(i)));
  }
  return vs;
}

// Aux clones
DirMultSPAux* DirMultSPAux::copy_help(ForwardingMap* m) const
{
  DirMultSPAux* answer = new DirMultSPAux(*this);
  (*m)[this] = answer;
  return answer;
}

UCDirMultSPAux* UCDirMultSPAux::copy_help(ForwardingMap* m) const
{
  UCDirMultSPAux* answer = new UCDirMultSPAux(*this);
  (*m)[this] = answer;
  return answer;
}
