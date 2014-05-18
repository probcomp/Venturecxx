#ifndef GKERNEL_HMC_H
#define GKERNEL_HMC_H

#include "gkernel.h"
#include "value.h"
#include "values.h"
#include "gkernels/inplace.h"
#include <gsl/gsl_rng.h>

struct ConcreteTrace;
struct Scaffold;
struct DB;


struct GradientOfRegen {
  GradientOfRegen(ConcreteTrace * trace, shared_ptr<Scaffold> scaffold);
  vector<VentureValuePtr> operator()(const vector<VentureValuePtr>& values);
  double fixed_regen(const std::vector<VentureValuePtr>& values);

  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;

  shared_ptr<gsl_rng> rngstate;
};


/* hamiltonian dynamics */
class HMCGKernel : public GKernel, public InPlaceGKernel
{
public:
  HMCGKernel(double epsilon, int steps);

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  pair<VentureValuePtr, double> evolve(GradientOfRegen& grad, const VentureValuePtr& start_q, const VentureValuePtr& start_grad_q, 
                      const VentureValuePtr& start_p);
  double kinetic(const VentureValuePtr momenta) const;
  VentureValuePtr sampleMomenta(VentureValuePtr currentValues, gsl_rng * rng) const;

 private:
  VentureValuePtr epsilon;
  VentureValuePtr steps;
};

#endif
