// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

#include "gkernels/pgibbs.h"
#include "detach.h"
#include "utils.h"
#include <math.h>
#include "particle.h"
#include "consistency.h"
#include "regen.h"
#include "db.h"
#include "concrete_trace.h"
#include "rng.h"

#include <boost/thread.hpp>

struct PGibbsWorker
{
  PGibbsWorker(boost::shared_ptr<Scaffold> scaffold): scaffold(scaffold) {}

  void doPGibbsInitial(ConcreteTrace * trace, unsigned long seed)
  {
    particle = boost::shared_ptr<Particle>(new Particle(trace, seed));
    weight = regenAndAttach(particle.get(), scaffold->border[0], scaffold,
                            false, boost::shared_ptr<DB>(new DB()), nullGradients);
  }

  void doPGibbsPropagate(vector<boost::shared_ptr<Particle> > & oldParticles,
                         const vector<double> & sums, unsigned long seed, int t)
  {
    RNGbox rng(gsl_rng_mt19937);
    rng.set_seed(seed);
    size_t parentIndex = samplePartialSums(sums, rng.get_rng());
    particle = boost::shared_ptr<Particle>(
      new Particle(oldParticles[parentIndex], gsl_rng_get(rng.get_rng())));
    weight = regenAndAttach(particle.get(), scaffold->border[t], scaffold,
                            false, boost::shared_ptr<DB>(new DB()), nullGradients);
  }

  boost::shared_ptr<Scaffold> scaffold;

  boost::shared_ptr<map<Node*, Gradient> > nullGradients;

  boost::shared_ptr<Particle> particle;
  double weight;
};


pair<Trace*, double> PGibbsGKernel::propose(
    ConcreteTrace * trace, const boost::shared_ptr<Scaffold> & scaffold)
{
  // assertTrace(self.trace, self.scaffold)
  this->scaffold = scaffold;

  size_t numBorderGroups = scaffold->border.size();

  vector<double> rhoWeights(numBorderGroups);
  vector<boost::shared_ptr<DB> > rhoDBs(numBorderGroups);

  for (long borderGroup = numBorderGroups; --borderGroup >= 0;) {
    pair<double, boost::shared_ptr<DB> > weightAndDB =
      detachAndExtract(trace, scaffold->border[borderGroup], scaffold);
    rhoWeights[borderGroup] = weightAndDB.first;
    rhoDBs[borderGroup] = weightAndDB.second;
  }

  assertTorus(scaffold);
  // Simulate and calculate initial xiWeights

  boost::shared_ptr<map<Node*, Gradient> > nullGradients;

  vector<double> particleWeights(numNewParticles + 1);
  vector<boost::shared_ptr<Particle> > particles(numNewParticles + 1);
  vector<boost::shared_ptr<PGibbsWorker> > workers(numNewParticles);
  if (inParallel) {
    vector<boost::thread*> threads(numNewParticles);
    for (size_t p = 0; p < numNewParticles; ++p) {
      workers[p] = boost::shared_ptr<PGibbsWorker>(new PGibbsWorker(scaffold));
      const unsigned long seed = gsl_rng_get(trace->getRNG());
      boost::function<void()> th_func =
        boost::bind(&PGibbsWorker::doPGibbsInitial, workers[p], trace, seed);
      threads[p] = new boost::thread(th_func);
    }
    for (size_t p = 0; p < numNewParticles; ++p) {
      threads[p]->join();
      particles[p] = workers[p]->particle;
      particleWeights[p] = workers[p]->weight;

      delete threads[p];
    }
  } else {
    for (size_t p = 0; p < numNewParticles; ++p) {
      workers[p] = boost::shared_ptr<PGibbsWorker>(new PGibbsWorker(scaffold));
      workers[p]->doPGibbsInitial(trace, gsl_rng_get(trace->getRNG()));
      particles[p] = workers[p]->particle;
      particleWeights[p] = workers[p]->weight;

    }
  }
  particles[numNewParticles] = boost::shared_ptr<Particle>(
    new Particle(trace, gsl_rng_get(trace->getRNG())));
  particleWeights[numNewParticles] =
    regenAndAttach(particles[numNewParticles].get(), scaffold->border[0],
                   scaffold, true, rhoDBs[0], nullGradients);

  // assert_almost_equal(particleWeights[P], rhoWeights[0])

  for (size_t borderGroup = 1; borderGroup < numBorderGroups; ++borderGroup) {
    vector<boost::shared_ptr<Particle> > newParticles(numNewParticles + 1);
    vector<double> newParticleWeights(numNewParticles + 1);

    // create partial sums in order to efficiently sample from ALL particles
    vector<double> sums = computePartialSums(mapExpUptoMultConstant(particleWeights));

    if (inParallel) {
      vector<boost::thread*> threads(numNewParticles);
      for (size_t p = 0; p < numNewParticles; ++p) {
        workers[p] = boost::shared_ptr<PGibbsWorker>(new PGibbsWorker(scaffold));
        boost::function<void()> th_func = boost::bind(
          &PGibbsWorker::doPGibbsPropagate, workers[p], particles, sums,
          gsl_rng_get(trace->getRNG()), borderGroup);
        threads[p] = new boost::thread(th_func);
      }

      newParticles[numNewParticles] = boost::shared_ptr<Particle>(
        new Particle(particles[numNewParticles],
		     gsl_rng_get(trace->getRNG())));
      newParticleWeights[numNewParticles] =
        regenAndAttach(newParticles[numNewParticles].get(),
                       scaffold->border[borderGroup], scaffold, true,
                       rhoDBs[borderGroup], nullGradients);

      for (size_t p = 0; p < numNewParticles; ++p) {
        threads[p]->join();
        newParticles[p] = workers[p]->particle;
        newParticleWeights[p] = workers[p]->weight;
        delete threads[p];
      }
    } else {
      for (size_t p = 0; p < numNewParticles; ++p) {
        workers[p] = boost::shared_ptr<PGibbsWorker>(new PGibbsWorker(scaffold));
        workers[p]->doPGibbsPropagate(
          particles, sums, gsl_rng_get(trace->getRNG()),
	  borderGroup);
        newParticles[p] = workers[p]->particle;
        newParticleWeights[p] = workers[p]->weight;
      }

      newParticles[numNewParticles] = boost::shared_ptr<Particle>(
        new Particle(particles[numNewParticles],
		     gsl_rng_get(trace->getRNG())));
      newParticleWeights[numNewParticles] =
        regenAndAttach(newParticles[numNewParticles].get(),
                       scaffold->border[borderGroup], scaffold, true,
                       rhoDBs[borderGroup], nullGradients);
    }
    // assert_almost_equal(newParticleWeights[P], rhoWeights[t])

    particles = newParticles;
    particleWeights = newParticleWeights;

  }

  oldParticle = particles.back();

  // Now sample a NEW particle in proportion to its weight
  vector<double> particleWeightsNoRho = particleWeights;
  particleWeightsNoRho.pop_back();
  size_t finalIndex = sampleCategorical(mapExpUptoMultConstant(particleWeightsNoRho),
                                        trace->getRNG());
  // assert finalIndex < P
  finalParticle = particles[finalIndex];

  // Remove the weight of the chosen xi from the list instead of
  // trying to subtract in logspace to prevent catastrophic
  // cancellation like the non-functional case
  vector<double> particleWeightsNoXi = particleWeights;
  particleWeightsNoXi.erase(particleWeightsNoXi.begin() + finalIndex);

  double weightMinusXi = logSumExp(particleWeightsNoXi);
  double weightMinusRho = logSumExp(particleWeightsNoRho);
  double alpha = weightMinusRho - weightMinusXi;

  return make_pair(finalParticle.get(), alpha);
}

int PGibbsGKernel::accept()
{
  finalParticle->commit();
  // assertTrace(self.trace, self.scaffold)
  return this->scaffold->numAffectedNodes();
}

int PGibbsGKernel::reject()
{
  oldParticle->commit();
  // assertTrace(self.trace, self.scaffold)
  return this->scaffold->numAffectedNodes();
}
