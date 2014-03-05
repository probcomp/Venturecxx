#ifndef GKERNEL_MH_H
#define GKERNEL_MH_H

#include "gkernel.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;

/* single-site Metropolis-Hastings */
struct MHGKernel : GKernel
{

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  
  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;
  shared_ptr<DB> rhoDB;

};
#endif
