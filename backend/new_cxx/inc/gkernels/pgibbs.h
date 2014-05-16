#ifndef GKERNEL_PGIBBS_H
#define GKERNEL_PGIBBS_H

#include "gkernel.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;
struct Particle;

/* Functional particle gibbs. */
struct PGibbsGKernel : GKernel
{
  PGibbsGKernel(size_t numNewParticles,bool inParallel): inParallel(inParallel), numNewParticles(numNewParticles) {}

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  
  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;
  shared_ptr<DB> rhoDB;

  bool inParallel;
  
  /* Does not include the old particle. */
  size_t numNewParticles;
private:
  
  /* The particle generated from the old trace. */
  shared_ptr<Particle> oldParticle;
  
  /* The particle chosen by propose(). */
  shared_ptr<Particle> finalParticle;
};
#endif
