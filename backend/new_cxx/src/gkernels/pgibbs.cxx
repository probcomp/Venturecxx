#include "gkernels/pgibbs.h"
#include "detach.h"
#include "utils.h"
#include <math.h>
#include "particle.h"
#include "consistency.h"
#include "regen.h"
#include "db.h"
#include "concrete_trace.h"

#include <boost/thread.hpp>

struct PGibbsWorker
{
  PGibbsWorker(shared_ptr<Scaffold> scaffold): scaffold(scaffold) {}

  void doPGibbsInitial(ConcreteTrace * trace)
  {
    particle = shared_ptr<Particle>(new Particle(trace));
    weight = regenAndAttach(particle.get(),scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),nullGradients);
  }

  void doPGibbsPropagate(vector<shared_ptr<Particle> > & oldParticles, const vector<double> & sums, gsl_rng * rng, int t)
  {
    size_t parentIndex = samplePartialSums(sums, rng);
    particle = shared_ptr<Particle>(new Particle(oldParticles[parentIndex]));
    weight = regenAndAttach(particle.get(),scaffold->border[t],scaffold,false,shared_ptr<DB>(new DB()),nullGradients);
  }

  shared_ptr<Scaffold> scaffold;

  shared_ptr<map<Node*,Gradient> > nullGradients;

  shared_ptr<Particle> particle;
  double weight;
};


pair<Trace*,double> PGibbsGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  // assertTrace(self.trace,self.scaffold)

  size_t numBorderGroups = scaffold->border.size();

  vector<double> rhoWeights(numBorderGroups);
  vector<shared_ptr<DB> > rhoDBs(numBorderGroups);

  for (long borderGroup = numBorderGroups; --borderGroup >= 0;)
  {
    pair<double,shared_ptr<DB> > weightAndDB = detachAndExtract(trace,scaffold->border[borderGroup],scaffold);
    rhoWeights[borderGroup] = weightAndDB.first;
    rhoDBs[borderGroup] = weightAndDB.second;
  }

  assertTorus(scaffold);
  // Simulate and calculate initial xiWeights

  shared_ptr<map<Node*,Gradient> > nullGradients;

  vector<shared_ptr<Particle> > particles(numNewParticles + 1);
  vector<double> particleWeights(numNewParticles + 1);
  vector<boost::thread*> threads(numNewParticles);
  vector<PGibbsWorker*> workers(numNewParticles);

  for (size_t p = 0; p < numNewParticles; ++p)
  {
    workers[p] = new PGibbsWorker(scaffold);
    boost::function<void()> th_func = boost::bind(&PGibbsWorker::doPGibbsInitial,workers[p],trace);
    threads[p] = new boost::thread(th_func);
    if (!inParallel) { threads[p]->join(); }
  }
  
  particles[numNewParticles] = shared_ptr<Particle>(new Particle(trace));
  particleWeights[numNewParticles] =
    regenAndAttach(particles[numNewParticles].get(),scaffold->border[0],scaffold,true,rhoDBs[0],nullGradients);

  for (size_t p = 0; p < numNewParticles; ++p)
  {
    if (inParallel) { threads[p]->join(); }
    threads[p]->join();
    particles[p] = workers[p]->particle;
    particleWeights[p] = workers[p]->weight;
    delete workers[p];
    delete threads[p];
  }

  // assert_almost_equal(particleWeights[P],rhoWeights[0])

  for (size_t borderGroup = 1; borderGroup < numBorderGroups; ++borderGroup)
  {
    vector<shared_ptr<Particle> > newParticles(numNewParticles + 1);
    vector<double> newParticleWeights(numNewParticles + 1);
    
    // create partial sums in order to efficiently sample from ALL particles
    vector<double> sums = computePartialSums(mapExpUptoMultConstant(particleWeights));

    for (size_t p = 0; p < numNewParticles; ++p)
      {
	workers[p] = new PGibbsWorker(scaffold);
	boost::function<void()> th_func = boost::bind(&PGibbsWorker::doPGibbsPropagate,workers[p],particles,sums,trace->getRNG(),borderGroup);
	threads[p] = new boost::thread(th_func);
	if (!inParallel) { threads[p]->join(); }
      }
    
    newParticles[numNewParticles] = shared_ptr<Particle>(new Particle(particles[numNewParticles]));
    newParticleWeights[numNewParticles] =
      regenAndAttach(newParticles[numNewParticles].get(),scaffold->border[borderGroup],scaffold,true,rhoDBs[borderGroup],nullGradients);
    // assert_almost_equal(newParticleWeights[P],rhoWeights[t])

    for (size_t p = 0; p < numNewParticles; ++p)
      {
	if (inParallel) { threads[p]->join(); }
	newParticles[p] = workers[p]->particle;
	newParticleWeights[p] = workers[p]->weight;
	delete workers[p];
	delete threads[p];
      }

    particles = newParticles;
    particleWeights = newParticleWeights;

  }
  
  oldParticle = particles.back();
  
  // Now sample a NEW particle in proportion to its weight
  vector<double> particleWeightsNoRho = particleWeights;
  particleWeightsNoRho.pop_back();
  size_t finalIndex = sampleCategorical(mapExpUptoMultConstant(particleWeightsNoRho), trace->getRNG());
  // assert finalIndex < P
  finalParticle = particles[finalIndex];
  
  // Remove the weight of the chosen xi from the list instead of
  // trying to subtract in logspace to prevent catastrophic
  // cancellation like the non-functional case
  vector<double> particleWeightsNoXi = particleWeights;
  particleWeightsNoXi.erase(particleWeightsNoXi.begin() + finalIndex);

  double weightMinusXi = logaddexp(particleWeightsNoXi);
  double weightMinusRho = logaddexp(particleWeightsNoRho);
  double alpha = weightMinusRho - weightMinusXi;
  
  return make_pair(finalParticle.get(),alpha);
}

void PGibbsGKernel::accept()
{
  finalParticle->commit();
  // assertTrace(self.trace,self.scaffold)    
}

void PGibbsGKernel::reject()
{
  oldParticle->commit();
  // assertTrace(self.trace,self.scaffold)
}
