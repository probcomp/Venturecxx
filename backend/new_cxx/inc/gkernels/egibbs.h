#ifndef GKERNEL_EGIBBS_H
#define GKERNEL_EGIBBS_H

#include "gkernel.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;
struct Particle;

/* enumerative Gibbs */
struct EnumerativeGibbsGKernel : GKernel
{
 EnumerativeGibbsGKernel(bool inParallel): inParallel(inParallel) {}
  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  
  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;
  
  /* The old DB */
  shared_ptr<DB> rhoDB;
  
  /* The particle chosen by propose(). */
  shared_ptr<Particle> finalParticle;

  bool inParallel;

  // An overridable hook for enumerative MAP
  virtual shared_ptr<Particle> selectParticle(const vector<shared_ptr<Particle> >& particles,
                                              const vector<double>& particleWeights,
                                              ConcreteTrace* trace) const;
};

struct EnumerativeMAPGKernel : EnumerativeGibbsGKernel
{
  EnumerativeMAPGKernel(bool inParallel): EnumerativeGibbsGKernel(inParallel) {}
  shared_ptr<Particle> selectParticle(const vector<shared_ptr<Particle> >& particles,
                                      const vector<double>& particleWeights,
                                      ConcreteTrace* trace) const;

};
#endif
