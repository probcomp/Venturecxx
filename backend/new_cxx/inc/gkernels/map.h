#ifndef GKERNEL_MAP_H
#define GKERNEL_MAP_H

#include "gkernel.h"
#include "gkernels/inplace.h"
#include <gsl/gsl_rng.h>
#include "gkernels/hmc.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;

/* hamiltonian dynamics */
class MAPGKernel : public GKernel, public InPlaceGKernel
{
public:
  MAPGKernel(double epsilon, int steps);

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  vector<VentureValuePtr> evolve(GradientOfRegen& grad, vector<VentureValuePtr>& currentValues, const vector<VentureValuePtr>& start_grad);
  void accept();
  void reject();

 private:
  shared_ptr<gsl_rng> rng; 	
  unsigned int seed;
  
  VentureValuePtr epsilon;
  VentureValuePtr steps;
};
#endif
