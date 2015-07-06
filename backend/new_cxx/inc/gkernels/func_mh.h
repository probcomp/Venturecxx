// Copyright (c) 2014 MIT Probabilistic Computing Project.
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

  pair<Trace*,double> propose(ConcreteTrace * trace,boost::shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  
  ConcreteTrace * trace;
  boost::shared_ptr<Scaffold> scaffold;
  boost::shared_ptr<DB> rhoDB;
  boost::shared_ptr<Particle> particle;
};
#endif
