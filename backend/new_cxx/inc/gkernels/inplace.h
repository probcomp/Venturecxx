#ifndef GKERNEL_INPLACE_H
#define GKERNEL_INPLACE_H

#include "gkernel.h"
#include <gsl/gsl_rng.h>

struct ConcreteTrace;
struct Scaffold;
struct DB;

/* A In-Place Operator */
class InPlaceGKernel
{
public:
  InPlaceGKernel();

  double prepare(ConcreteTrace * trace, shared_ptr<Scaffold> scaffold, bool compute_gradient = false);

  void accept();
  void reject();
};
#endif
