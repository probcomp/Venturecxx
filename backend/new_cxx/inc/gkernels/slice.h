// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

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

  pair<Trace*,double> propose(ConcreteTrace * trace,boost::shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();

  ConcreteTrace * trace;
  boost::shared_ptr<Scaffold> scaffold;
  boost::shared_ptr<PSP> psp;
  ApplicationNode * pnode;

  unsigned int seed;

  /* The old DB */
  boost::shared_ptr<DB> rhoDB;

};
#endif
