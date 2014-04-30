#ifndef GKERNEL_HMC_H
#define GKERNEL_HMC_H

#include "gkernel.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;

/* hamiltonian dynamics */
struct HMCGKernel : GKernel
{

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  
  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;
  shared_ptr<DB> rhoDB;
};
#endif
