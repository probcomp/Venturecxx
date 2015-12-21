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

#include "sps/hmm.h"
#include "args.h"
#include "sprecord.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <boost/foreach.hpp>
#include <algorithm>

VectorXd vvToEigenVector(VentureValue * value);
MatrixXd vvToEigenMatrix(VentureValue * value);
uint32_t indexOfOne(const VectorXd & v);
VectorXd sampleVectorXd(const VectorXd & v,gsl_rng * rng);
uint32_t sampleVector(const VectorXd & v,gsl_rng * rng);
VectorXd normalizedVectorXd(VectorXd & v);

/* MakeUncollapsedHMMSP */

VentureValuePtr MakeUncollapsedHMMOutputPSP::simulate(shared_ptr<Args> args,
                                                      gsl_rng * rng) const
{
  MatrixXd p0 = args->operandValues[0]->getMatrix();
  MatrixXd T = args->operandValues[1]->getMatrix();
  MatrixXd O = args->operandValues[2]->getMatrix();
  return VentureValuePtr(
    new VentureSPRecord(
      new UncollapsedHMMSP(
        new UncollapsedHMMRequestPSP(),
        new UncollapsedHMMOutputPSP(O),
        p0,
        T,
        O),
      new HMMSPAux()
      ));
}

/* UncollapsedHMMSP */
UncollapsedHMMSP::UncollapsedHMMSP(PSP * requestPSP, PSP * outputPSP,
                                   MatrixXd p0, MatrixXd T, MatrixXd O):
  SP(requestPSP,outputPSP), p0(p0), T(T), O(O) {}

shared_ptr<LatentDB> UncollapsedHMMSP::constructLatentDB() const
{
  return shared_ptr<LatentDB>(new HMMLatentDB());
}

double UncollapsedHMMSP::simulateLatents(shared_ptr<SPAux> spaux,
                                         shared_ptr<LSR> lsr,
                                         bool shouldRestore,
                                         shared_ptr<LatentDB> latentDB,
                                         gsl_rng * rng) const
{
  /* if should restore, restore, otherwise do not assert latentDB */
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(spaux);
  assert(aux);

  shared_ptr<HMMLSR> request = dynamic_pointer_cast<HMMLSR>(lsr);
  assert(request);

  shared_ptr<HMMLatentDB> latents;
  if (latentDB)
  {
    latents = dynamic_pointer_cast<HMMLatentDB>(latentDB);
    assert(latents);
  }

  /* No matter what the request is, we must sample the first latent if
     we have not already done so. */
  if (aux->xs.empty())
  {
    if (shouldRestore) { aux->xs.push_back(latents->xs[0]); }
    else { aux->xs.push_back(sampleVectorXd(p0,rng)); }
  }

  if (aux->xs.size() <= request->index)
  {
    for (size_t i = aux->xs.size(); i <= request->index; ++i)
    {
      MatrixXd sample;

      if (shouldRestore) { sample = latents->xs[i]; }
      else { sample = sampleVectorXd(T * aux->xs.back(),rng); }
      aux->xs.push_back(sample);
    }
  }
  assert(aux->xs.size() > request->index);
  return 0;
}

double UncollapsedHMMSP::detachLatents(shared_ptr<SPAux> spaux,
                                       shared_ptr<LSR> lsr,
                                       shared_ptr<LatentDB> latentDB) const
{
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(spaux);
  assert(aux);

  shared_ptr<HMMLSR> request = dynamic_pointer_cast<HMMLSR>(lsr);
  assert(request);

  shared_ptr<HMMLatentDB> latents = dynamic_pointer_cast<HMMLatentDB>(latentDB);
  assert(latents);

  if (aux->xs.size() == request->index + 1 &&
      !aux->os.count(request->index))
  {
    if (aux->os.empty())
    {
      for (size_t i = 0; i < aux->xs.size(); ++i)
      { latents->xs[i] = aux->xs[i]; }
      aux->xs.clear();
    }
    else
    {
      uint32_t maxObservation = (*(max_element(aux->os.begin(),aux->os.end()))).first;
      for (size_t i = aux->xs.size()-1; i > maxObservation; --i)
      {
        latents->xs[i] = aux->xs.back();
        aux->xs.pop_back();
      }
      assert(aux->xs.size() == maxObservation + 1);
    }
  }
  return 0;
}

void UncollapsedHMMSP::AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,
                               gsl_rng * rng) const
{
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(spAux);
  assert(aux);

  if (aux->os.empty()) { return; }

  uint32_t maxObservation = (*(max_element(aux->os.begin(),aux->os.end()))).first;
  vector<VectorXd> fs(1,p0);

  /* Forwards filtering */
  for (size_t i = 1; i <= maxObservation; ++i)
  {
    VectorXd f = T * fs[i-1];
    if (aux->os.count(i))
    {
      assert(aux->os[i].size() == 1);
      BOOST_FOREACH (uint32_t j, aux->os[i])
      {
        f = O.row(j).asDiagonal() * f;
      }
    }
    fs.push_back(normalizedVectorXd(f));
  }

  /* Backwards sampling */
  aux->xs.resize(maxObservation + 1);

  aux->xs[maxObservation] = sampleVectorXd(fs[maxObservation],rng);
  for (int i = maxObservation-1; i >= 0; --i)
  {
    size_t rowIndex = indexOfOne(aux->xs[i+1]);
    MatrixXd T_i = T.row(rowIndex).asDiagonal();
    VectorXd gamma = T_i * fs[i];
    aux->xs[i] = sampleVectorXd(normalizedVectorXd(gamma),rng);
  }
}


/* UncollapsedHMMOutputPSP */

UncollapsedHMMOutputPSP::UncollapsedHMMOutputPSP(MatrixXd O): O(O) {}


VentureValuePtr UncollapsedHMMOutputPSP::simulate(shared_ptr<Args> args,
                                                  gsl_rng * rng) const
{
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(args->spAux);
  assert(aux);
  int index = args->operandValues[0]->getInt();
  assert(aux->xs.size() > static_cast<uint32_t>(index));

  return VentureValuePtr(new VentureAtom(sampleVector(O * aux->xs[index],rng)));
}

double UncollapsedHMMOutputPSP::logDensity(VentureValuePtr value,
                                           shared_ptr<Args> args) const
{
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(args->spAux);
  assert(aux);

  int out = value->getInt();
  int in = args->operandValues[0]->getInt();

  assert(aux->xs.size() > static_cast<uint32_t>(in));

  VectorXd dist = O * aux->xs[in];
  return log(dist[out]);
}

void UncollapsedHMMOutputPSP::incorporate(VentureValuePtr value,
                                          shared_ptr<Args> args) const
{
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(args->spAux);
  assert(aux);

  int out = value->getInt();
  int in = args->operandValues[0]->getInt();

  /* Register observation */
  aux->os[in].push_back(out);
}

void UncollapsedHMMOutputPSP::unincorporate(VentureValuePtr value,
                                            shared_ptr<Args> args) const
{
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(args->spAux);
  assert(aux);

  int out = value->getInt();
  int in = args->operandValues[0]->getInt();

  vector<uint32_t> & iObs = aux->os[in];
  size_t oldSize = iObs.size();

  /* Remove observation. */
  iObs.erase(std::find(iObs.begin(),iObs.end(),out));
  assert(oldSize == iObs.size() + 1);
  if (iObs.empty()) { aux->os.erase(in); }
}


/* UncollapsedHMMRequestPSP */

VentureValuePtr UncollapsedHMMRequestPSP::simulate(shared_ptr<Args> args,
                                                   gsl_rng * rng) const
{
  int in = args->operandValues[0]->getInt();
  vector<shared_ptr<LSR> > lsrs;
  lsrs.push_back(shared_ptr<LSR>(new HMMLSR(in)));
  return VentureValuePtr(new VentureRequest(lsrs));
}



/* Matrix utils */
/* Helpers */

VectorXd vvToEigenVector(VentureValue * value)
{
  vector<VentureValuePtr> vs = value->getArray();

  size_t len = vs.size();
  VectorXd v(len);

  for (size_t i = 0; i < len; ++i)
  {
    v(i) = vs[i]->getDouble();
  }
  return v;
}

MatrixXd vvToEigenMatrix(VentureValue * value)
{
  uint32_t rows, cols;

  vector<VentureValuePtr> allRows = value->getArray();
  rows = allRows.size();
  assert(rows > 0);

  vector<VentureValuePtr> row0 = allRows[0]->getArray();
  cols = row0.size();
  assert(cols > 0);

  MatrixXd M(rows,cols);

  for (size_t i = 0; i < rows; ++i)
  {
    vector<VentureValuePtr> row_i = allRows[i]->getArray();
    assert(cols == row_i.size());

    for (size_t j = 0; j < cols; ++j)
    {
      M(i,j) = row_i[j]->getDouble();
    }
  }
  return M;
}

uint32_t indexOfOne(const VectorXd & v)
{
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i)
  {
    if (v[i] == 1) { return i; }
    else { assert(v[i] == 0); }
  }
  assert(false);
  return -1;
}

VectorXd sampleVectorXd(const VectorXd & v,gsl_rng * rng)
{
  VectorXd sample(v.size());
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i) { sample[i] = 0; }

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < len; ++i)
  {
    sum += v[i];
    if (u <= sum)
    {
      sample[i] = 1;
      return sample;
    }
  }
  assert(false);
  return sample;
}

uint32_t sampleVector(const VectorXd & v,gsl_rng * rng)
{
  double u = gsl_ran_flat(rng,0.0,1.0);

  double sum = 0.0;
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i)
  {
    sum += v[i];
    if (u <= sum) { return i; }
  }
  cout << "sum should be 1: " << sum << endl;
  assert(false);
  return -1;
}

VectorXd normalizedVectorXd(VectorXd & v)
{

  size_t len = v.size();
  double sum = 0;
  for (size_t i = 0; i < len; ++i) { sum += v[i]; }

  VectorXd newVector(len);
  for (size_t i = 0; i < len; ++i) { newVector[i] = v[i] / sum; }
  return newVector;
}

SPAux* HMMSPAux::copy_help(ForwardingMap* m) const
{
  return new HMMSPAux(*this);
}
