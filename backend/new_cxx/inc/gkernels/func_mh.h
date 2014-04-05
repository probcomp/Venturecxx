#ifndef GKERNEL_FUNC_MH_H
#define GKERNEL_FUNC_MH_H

#include "gkernel.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;
struct Particle;

/* single-site Metropolis-Hastings */
struct FuncMHGKernel : GKernel
{

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  
  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;
  shared_ptr<DB> rhoDB;
  shared_ptr<Particle> particle;
};
#endif
