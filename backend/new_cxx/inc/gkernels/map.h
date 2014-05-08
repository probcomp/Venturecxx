#ifndef GKERNEL_MAP_H
#define GKERNEL_MAP_H

#include "gkernel.h"
#include <gsl/gsl_rng.h>

struct ConcreteTrace;
struct Scaffold;
struct DB;

/* hamiltonian dynamics */
class MAPGKernel : GKernel
{
public:
  MAPGKernel();

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();

 private:
  shared_ptr<gsl_rng> rng; 	
  unsigned int seed;
  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;
  shared_ptr<DB> rhoDB;
};
#endif
