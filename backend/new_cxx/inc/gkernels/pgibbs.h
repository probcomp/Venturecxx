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

#ifndef GKERNEL_PGIBBS_H
#define GKERNEL_PGIBBS_H

#include "gkernel.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;
struct Particle;

/* Functional particle gibbs. */
struct PGibbsGKernel : GKernel
{
  PGibbsGKernel(size_t numNewParticles,bool inParallel): inParallel(inParallel), numNewParticles(numNewParticles) {}

  pair<Trace*,double> propose(ConcreteTrace * trace,boost::shared_ptr<Scaffold> scaffold);
  void accept();
  void reject();
  
  ConcreteTrace * trace;
  boost::shared_ptr<Scaffold> scaffold;
  boost::shared_ptr<DB> rhoDB;

  bool inParallel;
  
  /* Does not include the old particle. */
  size_t numNewParticles;
private:
  
  /* The particle generated from the old trace. */
  boost::shared_ptr<Particle> oldParticle;
  
  /* The particle chosen by propose(). */
  boost::shared_ptr<Particle> finalParticle;
};
#endif
