#include "gkernels/pgibbs.h"
#include "detach.h"
#include "utils.h"
#include <math.h>
#include "particle.h"
#include "regen.h"
#include "db.h"
#include "concrete_trace.h"

pair<Trace*,double> PGibbsGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  // assertTrace(self.trace,self.scaffold)

  size_t numBorderGroups = scaffold->border.size();

  vector<double> rhoWeights(numBorderGroups);
  vector<shared_ptr<DB> > rhoDBs(numBorderGroups);

  for (int borderGroup = numBorderGroups; --borderGroup >= 0;)
  {
    pair<double,shared_ptr<DB> > weightAndDB = detachAndExtract(trace,scaffold->border[borderGroup],scaffold);
    rhoWeights[borderGroup] = weightAndDB.first;
    rhoDBs[borderGroup] = weightAndDB.second;
  }

  // assertTorus(scaffold)

  // Simulate and calculate initial xiWeights

  shared_ptr<map<Node*,Gradient> > nullGradients;
  
  vector<shared_ptr<Particle> > particles(numParticles);
  vector<double> particleWeights(numParticles);
  
  for (size_t p = 0; p < numParticles; ++p)
  {
    particles[p] = shared_ptr<Particle>(new Particle(trace));
    particleWeights[p] =
      regenAndAttach(particles[p].get(),scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),nullGradients);
  }
  
  particles[numParticles] = shared_ptr<Particle>(new Particle(trace));
  particleWeights[numParticles] =
    regenAndAttach(particles[numParticles].get(),scaffold->border[0],scaffold,true,rhoDBs[0],nullGradients);
  // assert_almost_equal(particleWeights[P],rhoWeights[0])

  for (size_t borderGroup = 1; borderGroup < numBorderGroups; ++borderGroup)
  {
    vector<shared_ptr<Particle> > newParticles(numParticles);
    vector<double> newParticleWeights(numParticles);
    
    // create partial sums in order to efficiently sample from ALL particles
    vector<double> sums = computePartialSums(mapExp(particleWeights));
    
    // Sample new particle and propagate
    for (size_t p = 0; p < numParticles; ++p)
    {
      size_t parentIndex = samplePartialSums(sums, trace->getRNG());
      newParticles[p] = shared_ptr<Particle>(new Particle(particles[parentIndex]));
      newParticleWeights[p] =
        regenAndAttach(newParticles[p].get(),scaffold->border[borderGroup],scaffold,false,shared_ptr<DB>(new DB()),nullGradients);
    }
    
    newParticles[numParticles] = shared_ptr<Particle>(new Particle(particles[numParticles]));
    newParticleWeights[numParticles] =
      regenAndAttach(newParticles[numParticles].get(),scaffold->border[borderGroup],scaffold,true,rhoDBs[borderGroup],nullGradients);
    // assert_almost_equal(newParticleWeights[P],rhoWeights[t])
    particles = newParticles;
    particleWeights = newParticleWeights;
  }
  
  oldParticle = particles.back();
  
  // Now sample a NEW particle in proportion to its weight
  vector<double> particleWeightsNoRho = particleWeights;
  particleWeightsNoRho.pop_back();
  size_t finalIndex = sampleCategorical(mapExp(particleWeightsNoRho), trace->getRNG());
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
  
  // TODO Dan change all Trace* to shared_ptr<Trace>
  return make_pair(particles[finalIndex].get(),alpha);
}

void PGibbsGKernel::accept()
{
  // qfinalParticle->commit();
  // assertTrace(self.trace,self.scaffold)    
}

void PGibbsGKernel::reject()
{
  // oldParticle->commit();
  // assertTrace(self.trace,self.scaffold)
}
