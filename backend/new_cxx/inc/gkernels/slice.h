#ifndef GKERNELS_SLICE_H
#define GKERNELS_SLICE_H

#include "gkernel.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;
struct Particle;
struct PSP;
struct ApplicationNode;

/* Acknowledgements: The slice code is translated from Radford's Neal's implementation, which can be found at http://www.cs.toronto.edu/~radford/ftp/slice-R-prog */

/*  x0    Initial point
 *  g     Function returning the log of the probability density (plus constant)
 *  w     Size of the steps for creating interval (default 1)
 *  m     Limit on steps (default infinite)
 *  lower Lower bound on support of the distribution (default -Inf)
 *  upper Upper bound on support of the distribution (default +Inf)
 *  gx0   Value of g(x0), if known (default is not known)
 */

struct SliceGKernel : GKernel
{
  SliceGKernel(double w, int m): w(w), m(m) {}

  double w;
  int m;

  double computeLogDensity(double x);
  double sliceSample(double x0, double w, int m, double lower, double upper);

  pair<Trace*,double> propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();

  ConcreteTrace * trace;
  shared_ptr<Scaffold> scaffold;
  shared_ptr<PSP> psp;
  ApplicationNode * pnode;

  unsigned int seed;

  /* The old DB */
  shared_ptr<DB> rhoDB;

};
#endif
