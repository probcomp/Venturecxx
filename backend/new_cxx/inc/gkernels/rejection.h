#ifndef GKERNEL_REJECTION_H
#define GKERNEL_REJECTION_H

#include "gkernel.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;

struct BogoPossibilizeGKernel : GKernel
{

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  
  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;
  shared_ptr<DB> rhoDB;

};
#endif
